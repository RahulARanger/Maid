from json import loads, dumps
from urllib.request import urlopen
from dotenv import load_dotenv
from lxml import etree
from lxml.etree import _Element
from typing import Optional, Dict, TypedDict
from loguru import logger
from pathlib import Path
from maid.send_mail import send_email
from maid.utils import give_first_or_ntg, ARTIFACTS_FOLDER, find_difference
from datetime import datetime
from html import escape
load_dotenv()
FILE_NAME = "student_housing_aarhus_prev_results.json"


class Choice(TypedDict):
    Price: Optional[int]
    Address: Optional[str]
    Area: Optional[str]
    Date: Optional[str]
    Type: Optional[str]


class Response(TypedDict):
    Available: int
    Choices: Dict[str, Choice]


def open_html_template_string() -> str:
    return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>Student Housing Aarhus – Updates</title>
    <style>
      /* inlined + safe for most email clients */
      .container { max-width: 720px; margin: 0 auto; padding: 16px; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin: 0 0 16px 0; }
      h1, h2, h3 { margin: 0 0 8px 0; }
      .muted { color: #6b7280; font-size: 13px; }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #e5e7eb; }
      .pill--ok { background: #ecfdf5; border-color: #a7f3d0; }
      .pill--add { background: #ecfeff; border-color: #a5f3fc; }
      .pill--rm  { background: #fff1f2; border-color: #fecdd3; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 14px; vertical-align: top; }
      th { background: #f9fafb; }
      .row-add { background: #f0fdfa; }
      .row-rm  { background: #fff7ed; }
      a.btn { display:inline-block; padding:10px 14px; border-radius:10px; text-decoration:none; border:1px solid #111827; }
      .footer { margin-top: 16px; font-size: 12px; color: #6b7280; }
      @media (prefers-color-scheme: dark) {
        .card, th, td { border-color: #374151; }
        th { background: #111827; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <!-- HEADER -->
      <div class="card">
        <h1>Student Housing Aarhus – Updates</h1>
        <div class="muted">Snapshot: <!-- {snapshot_date} --></div>
        <p>
          <span class="pill pill--ok">Available now: <strong><!-- {current_available} --></strong></span>
          <span class="pill pill--add" style="margin-left:8px;">New: <strong><!-- {added_count} --></strong></span>
          <span class="pill pill--rm"  style="margin-left:8px;">Removed: <strong><!-- {removed_count} --></strong></span>
        </p>
        <p style="margin: 8px 0 0 0;">
          <a class="btn" href="https://studenthousingaarhus.com/all-available-housing">Open portal</a>
        </p>
      </div>

      <!-- NEW LISTINGS -->
      <!-- {added_section} -->

      <!-- REMOVED LISTINGS -->
      <!-- {removed_section} -->
      
      <!-- REST OF THE LISTINGS -->
      <!-- {rest_of_section} -->

      <div class="footer">
        You’re getting this because you track changes on studenthousingaarhus.com.  
        Tip: keys are built as “<em>Area</em> + <em>Price</em>”, so a price change will appear as “removed + new”.
      </div>
    </div>
  </body>
</html>
"""

def _row_html(key: str, item: dict, cls: str) -> str:
    return (
        f'<tr class="{cls}">'
        f"<td>{escape(item.get('Area','') or '')}</td>"
        f"<td>{escape(item.get('Price','') or '')}</td>"
        f"<td>{escape(item.get('Address','') or '')}</td>"
        f"<td>{escape(item.get('Date','') or '')}</td>"
        f"<td>{escape(item.get('Type','') or '')}</td>"
        f"<td>{escape(key)}</td>"
        "</tr>"
    )

def parse_things():
    with urlopen("https://studenthousingaarhus.com/all-available-housing") as request:
        html_content = request.read().decode('utf-8')
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_content, parser)

        available: list[_Element] = tree.xpath("//div[@class='avail_apt_small_card']")
        response: Response = {
            "Available": len(available),
            "Choices": {}
        }
        for choice in available:
            price = give_first_or_ntg(choice.xpath(".//div[@class='avail-apt-card-rent']/text()"))
            address = give_first_or_ntg(choice.xpath(".//div[@class='avail-apt-card-area']/text()"))
            response["Choices"][f"{address}{price}"] = {
                "Price": price,
                "Address": give_first_or_ntg(choice.xpath(".//div[@class='avail-apt-card-address']/text()")),
                "Area": address,
                "Date": give_first_or_ntg(choice.xpath(".//div[@class='avail-apt-card-date']/text()")),
                "Type": give_first_or_ntg(choice.xpath(".//div[@class='avail-apt-card-type']/text()"))
            }

    return response


def render_email_html(
        added_keys: set[str],
        removed_keys: set[str],
        previous_choices: dict,
        current_choices: dict,
        rest: set[str],
        current_available: int
) -> str:
    added_rows = "\n".join(
        _row_html(k, current_choices[k], "row-add") for k in added_keys
    )
    removed_rows = "\n".join(
        _row_html(k, previous_choices[k], "row-rm") for k in removed_keys
    )
    rest_of_rows = "\n".join(
        _row_html(k, current_choices[k], "row-rm") for k in rest
    )

    added_section = (
        f"""
        <div class="card">
          <h2>New listings</h2>
          <table role="table" aria-label="New listings">
            <thead><tr><th>Area</th><th>Price</th><th>Address</th><th>Date</th><th>Type</th><th>Key</th></tr></thead>
            <tbody>
              {added_rows or '<tr><td colspan="6" class="muted">No new listings.</td></tr>'}
            </tbody>
          </table>
        </div>
        """
    )

    removed_section = (
        f"""
        <div class="card">
          <h2>Removed listings</h2>
          <table role="table" aria-label="Removed listings">
            <thead><tr><th>Area</th><th>Price</th><th>Address</th><th>Date</th><th>Type</th><th>Key</th></tr></thead>
            <tbody>
              {removed_rows or '<tr><td colspan="6" class="muted">No removals.</td></tr>'}
            </tbody>
          </table>
        </div>
        """
    )

    rest_of_section = (
        f"""
            <div class="card">
              <h2>Rest of the listings</h2>
              <table role="table" aria-label="Rest of the listings">
                <thead><tr><th>Area</th><th>Price</th><th>Address</th><th>Date</th><th>Type</th><th>Key</th></tr></thead>
                <tbody>
                  {rest_of_rows or '<tr><td colspan="6" class="muted">No other listings.</td></tr>'}
                </tbody>
              </table>
            </div>
            """
    )

    template = open_html_template_string()

    html = (
        template
        .replace("<!-- {snapshot_date} -->", escape(datetime.now().strftime("%Y-%m-%d %H:%M")))
        .replace("<!-- {current_available} -->", str(current_available))
        .replace("<!-- {added_count} -->", str(len(added_keys)))
        .replace("<!-- {removed_count} -->", str(len(removed_keys)))
        .replace("<!-- {added_section} -->", added_section)
        .replace("<!-- {removed_section} -->", removed_section)
        .replace("<!-- {rest_of_section} -->", rest_of_section)
    )
    return html


def check_whats_up():
    diff_file = Path.cwd() / ARTIFACTS_FOLDER / FILE_NAME
    prev = {}
    if diff_file.exists():
        prev = loads(diff_file.read_text())

    current = parse_things()
    previous_choices = prev.get('Choices', {})
    current_choices = current.get('Choices', {})
    no_change, removed, added, rest = find_difference(previous_choices, current_choices)

    html = render_email_html(added, removed, previous_choices, current_choices, rest, current_available=current.get('Available', 0))

    if no_change:
        logger.info("There are no changes, so not sending any update.")
    else:
        sub = 'There are some changes in the Student Housing Portal'
        if added:
            sub = "There are new housing options in the Student Housing Portal!"
        elif removed:
            sub = "Some options were removed from the Student Housing Portal"

        send_email(sub, html)
        diff_file.write_text(dumps(current))

if __name__ == '__main__':
    check_whats_up()


import os
import json
import curses
import xml.etree.ElementTree as ET
import datetime
import requests


# Global constants
FEEDS_PATH = os.path.expanduser("~/.newspaperss/feeds.json")
FEEDS_DATA_PATH = os.path.expanduser("~/.newspaperss/feeds_data.json")


def fetch_rss_feed(url):
    response = requests.get(url, timeout=(5, 30))
    response.raise_for_status()
    return response.content


def read_json(path):
    abs_path = os.path.expanduser(path)

    with open(abs_path, encoding="UTF-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def xml_to_dict(xml_data):
    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    feed_title = channel.find("title").text
    feed_url = channel.find("link").text
    feed_items = channel.findall("item")

    parsed_items = []

    for item in feed_items:
        item_title = item.find("title").text
        item_pub_date = item.find("pubDate").text
        item_pub_date_datetime = datetime.datetime.strptime(
            item_pub_date,
            "%a, %d %b %Y %H:%M:%S %z"
        )
        formatted_item_pub_date = item_pub_date_datetime.strftime("%b %d")
        item_url = item.find("link").text
        item_description = item.find("description").text

        parsed_items.append({
            "item_title": item_title,
            "item_pub_date": formatted_item_pub_date,
            "item_url": item_url,
            "item_description": item_description
        })

    return {
        "feed_title": feed_title,
        "feed_url": feed_url,
        "feed_items": parsed_items
    }


def main(stdscr):
    # Initialize curses
    curses.initscr()

    # Hide the cursor
    curses.curs_set(0)

    stdscr_num_of_lines, stdscr_num_of_cols = stdscr.getmaxyx()

    feeds_data = read_json(FEEDS_DATA_PATH)
    num_of_feeds = len(feeds_data)

    title_win = curses.newwin(1, stdscr_num_of_cols, 0, 0)
    title_win.addstr(0, 0, "Newspaperss v0.1")
    title_win.refresh()

    feeds_win = None
    feed_items_win = None
    selected_feed = 0
    feeds_win_offset = 0

    # Flag to track if user is inside feed items window
    inside_feed_items_win = False

    if num_of_feeds == 0:
        stdscr.addstr(1, 0, "No feeds available => Add feeds to get started")
    else:
        feeds_win = curses.newpad(num_of_feeds, stdscr_num_of_cols)
        for idx, feed in enumerate(feeds_data):
            feed_title = feed["feed_title"]
            feeds_win.addstr(idx, 0, str(idx + 1))
            feeds_win.addstr(idx, 5, feed_title)
        feeds_win.chgat(selected_feed, 0, -1, curses.A_REVERSE)
        feeds_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)

    while True:
        # Flag to track if window resizing is happening
        resizing = False

        key = stdscr.getch()

        # Quit application if "q" is pressed
        if key == ord("q"):
            break

        # Set resizing flag to True if window is resized
        if key == curses.KEY_RESIZE:
            resizing = True

        # Refresh feeds when "R" is pressed, not by window resizing
        if key == ord("R") and not resizing:
            feeds = read_json(FEEDS_PATH)
            num_of_feeds = len(feeds)
            feeds_data_to_write = []
            feeds_win = curses.newpad(num_of_feeds, stdscr_num_of_cols)

            for feed in feeds:
                xml_data = fetch_rss_feed(feed["url"])
                feed_data_as_dict = xml_to_dict(xml_data)
                feeds_data_to_write.append(feed_data_as_dict)

            feeds_data = feeds_data_to_write

            with open(FEEDS_DATA_PATH, "w", encoding="UTF-8") as file:
                json.dump(feeds_data_to_write, file, ensure_ascii=False)

        if num_of_feeds != 0:
            # Clear feed items window when pressing "Esc" key
            if key == 27 and inside_feed_items_win:
                inside_feed_items_win = False
                feed_items_win.erase()
                feed_items_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)

            if inside_feed_items_win:
                continue

            # When pressing "Enter" key on a feed, display its feed items
            if key == 10:
                feeds_win.erase()

                feed_items = feeds_data[selected_feed]["feed_items"]
                num_of_feed_items = len(feed_items)
                feed_items_win = curses.newpad(num_of_feed_items, stdscr_num_of_cols)
                selected_feed_item = 0

                for idx, feed_item in enumerate(feed_items):
                    feed_items_win.addstr(idx, 0, str(idx + 1))
                    feed_items_win.addstr(idx, 5, feed_item["item_pub_date"])
                    feed_items_win.addstr(idx, 14, feed_item["item_title"])

                feed_items_win.chgat(selected_feed_item, 0, -1, curses.A_REVERSE)
                feed_items_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)

                inside_feed_items_win = True

                continue

            if key == ord("k"):
                if selected_feed > 0:
                    selected_feed -= 1

                    if feeds_win_offset > 0 and selected_feed == feeds_win_offset - 1:
                        feeds_win_offset -= 1

            if key == ord("j"):
                if selected_feed < num_of_feeds - 1:
                    selected_feed += 1

                    if selected_feed >= stdscr_num_of_lines - 1 + feeds_win_offset:
                        feeds_win_offset += 1

            feeds_win.erase()
            for idx, feed in enumerate(feeds_data):
                feed_title = feed["feed_title"]
                feeds_win.addstr(idx, 0, str(idx + 1))
                feeds_win.addstr(idx, 5, feed_title)
            feeds_win.chgat(selected_feed, 0, -1, curses.A_REVERSE)

            feeds_win.refresh(
                feeds_win_offset,
                0,
                1,
                0,
                stdscr_num_of_lines - 1,
                stdscr_num_of_cols
            )

        resizing = False


if __name__ == "__main__":
    # Set environment variable to prevent delay in escape key detection
    os.environ.setdefault("ESCDELAY", "0")

    curses.wrapper(main)

import os
import json
import curses
import enum
import xml.etree.ElementTree as ET
import datetime
import requests


# Global constants
FEEDS_PATH = os.path.expanduser("~/.newspaperss/feeds.json")
FEEDS_DATA_PATH = os.path.expanduser("~/.newspaperss/feeds_data.json")


# Enums for keys
class Keys(enum.Enum):
    QUIT = ord("q")
    REFRESH_ALL = ord("R")
    REFRESH = ord("r")
    BACK = 27
    ENTER = 10
    UP = ord("k")
    DOWN = ord("j")
    OPEN = ord("o")


# Window class that wraps around curses window for easier state management
class PadWindowWrapper:
    def __init__(self, pad, num_of_lines):
        self.pad = pad
        self.offset = 0
        self.num_of_lines = num_of_lines
        self.selected_line = 0


    def navigate_up(self):
        if self.selected_line > 0:
            self.selected_line -= 1

            if self.offset > 0 and self.selected_line == self.offset - 1:
                self.offset -= 1

        self.highlight_selected_line()


    def navigate_down(self):
        if self.selected_line < self.num_of_lines - 1:
            self.selected_line += 1

            if self.selected_line > self.num_of_lines - 1 + self.offset:
                self.offset += 1

        self.highlight_selected_line()


    def highlight_selected_line(self, attr=curses.A_REVERSE):
        self.pad.chgat(self.selected_line, 0, -1, attr)


    # Delegate all other attributes to the pad object, so that interaction 
    # with it is easier and more seemless
    def __getattr__(self, attr):
        return getattr(self.pad, attr)


def fetch_rss_feed(url):
    # Wait up to 5 seconds for connection and up to 30 seconds for data transfer
    response = requests.get(url, timeout=(5, 30))
    response.raise_for_status()
    return response.content


def read_json(path):
    with open(path, encoding="UTF-8") as file:
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

    # Extract relevant data from each feed item
    for item in feed_items:
        item_title = item.find("title").text
        item_pub_date = item.find("pubDate").text
        item_pub_date_datetime = datetime.datetime.strptime(
            item_pub_date, "%a, %d %b %Y %H:%M:%S %z"
        )

        formatted_item_pub_date = item_pub_date_datetime.strftime("%b %d")
        item_url = item.find("link").text
        item_description = item.find("description").text

        parsed_items.append({
            "item_url": item_url,
            "item_title": item_title,
            "item_description": item_description,
            "item_pub_date": formatted_item_pub_date
        })

    return {
        "feed_url": feed_url,
        "feed_title": feed_title,
        "feed_items": parsed_items
    }


def refresh_all_feeds_data():
    feeds = read_json(FEEDS_PATH)
    feeds_data_to_write = []

    for feed in feeds:
        xml_data = fetch_rss_feed(feed["url"])
        feed_data_as_dict = xml_to_dict(xml_data)
        feeds_data_to_write.append(feed_data_as_dict)

        with open(FEEDS_DATA_PATH, "w", encoding="UTF-8") as file:
            json.dump(feeds_data_to_write, file, ensure_ascii=False)

    return feeds_data_to_write


def resize_pad(pad_wrapper, new_num_of_lines, new_num_of_cols):
    new_pad = curses.newpad(new_num_of_lines, new_num_of_cols)

    pad_wrapper.pad = new_pad
    pad_wrapper.num_of_lines = new_num_of_lines


def display_feeds(feeds_win, feeds_data):
    for idx, feed in enumerate(feeds_data):
        feed_title = feed["feed_title"]
        feeds_win.addstr(idx, 0, str(idx + 1))
        feeds_win.addstr(idx, 5, feed_title)


def display_feed_items(feed_items_win, feed_items):
    for idx, feed_item in enumerate(feed_items):
        feed_items_win.addstr(idx, 0, str(idx + 1))
        feed_items_win.addstr(idx, 5, feed_item["item_pub_date"])
        feed_items_win.addstr(idx, 14, feed_item["item_title"])


def main(stdscr):
    # Initialize curses
    curses.initscr()

    # Hide the cursor
    curses.curs_set(0)

    stdscr.addstr(0, 0, "Newspaperss v0.1")

    stdscr_num_of_lines, stdscr_num_of_cols = stdscr.getmaxyx()

    feeds_data = read_json(FEEDS_DATA_PATH)
    num_of_feeds = len(feeds_data)

    feeds_win = None
    feed_items_win = None
    current_win = None
    feed_items = None

    if num_of_feeds == 0:
        stdscr.addstr(1, 0, "No feeds available => Add some feeds to get started")
    else:
        feeds_pad = curses.newpad(num_of_feeds, stdscr_num_of_cols)
        feeds_win = PadWindowWrapper((feeds_pad), num_of_feeds)
        display_feeds(feeds_win, feeds_data)
        feeds_win.highlight_selected_line()
        feeds_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)
        current_win = feeds_win

    while True:
        if current_win is not None:
            current_win.erase()

        # Flag to track if window resizing is happening
        resizing = False

        key = stdscr.getch()

        if key == Keys.QUIT.value: break

        # Set resizing flag to True if window is resized
        if key == curses.KEY_RESIZE:
            resizing = True

        # Refresh feeds when "R" is pressed, not by window resizing
        if key == Keys.REFRESH_ALL.value and not resizing:
            feeds_data = refresh_all_feeds_data() # GET NEW DATA
            num_of_feeds = len(feeds_data)

            if feeds_win is None:
                feeds_pad = curses.newpad(num_of_feeds, stdscr_num_of_cols)
                feeds_win = PadWindowWrapper((feeds_pad), num_of_feeds)
                current_win = feeds_win
            else:
                resize_pad(feeds_win, len(feeds_data), stdscr_num_of_cols)

        if num_of_feeds > 0:
            if current_win in (feeds_win, feed_items_win):
                if key == Keys.UP.value: current_win.navigate_up()
                elif key == Keys.DOWN.value: current_win.navigate_down()

            # When pressing "Enter" key on a feed, display its feed items
            if current_win == feeds_win and key == Keys.ENTER.value:
                feeds_win.erase()

                feed_items = feeds_data[feeds_win.selected_line]["feed_items"]
                num_of_feed_items = len(feed_items)

                feed_items_pad = curses.newpad(num_of_feed_items, stdscr_num_of_cols)
                feed_items_win = PadWindowWrapper(feed_items_pad, num_of_feed_items)

                current_win = feed_items_win

                display_feed_items(feed_items_win, feed_items)

                feed_items_win.highlight_selected_line()
                feed_items_win.refresh(
                    feed_items_win.offset,
                    0,
                    1,
                    0,
                    stdscr_num_of_lines - 1,
                    stdscr_num_of_cols
                )

                continue

            if key == Keys.BACK.value:
                if current_win == feed_items_win:
                    feed_items_win.erase()
                    feed_items_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)
                    current_win = feeds_win

            if current_win is not None:
                if current_win == feeds_win:
                    display_feeds(feeds_win, feeds_data)
                elif current_win == feed_items_win:
                    display_feed_items(feed_items_win, feed_items)

                current_win.highlight_selected_line()

                current_win.refresh(
                    current_win.offset,
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

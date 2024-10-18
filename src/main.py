import os
import json
import curses
import xml.etree.ElementTree as ET
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
    title = channel.find("title").text

    return {
        "title": title
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
    selected_feed = 0
    feeds_win_offset = 0

    if num_of_feeds == 0:
        stdscr.addstr(1, 0, "No feeds available => Add feeds to get started")
    else:
        feeds_win = curses.newpad(num_of_feeds, stdscr_num_of_cols)
        for idx, feed in enumerate(feeds_data):
            feed_title = feed["title"]
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
                feed_title = feed["title"]
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
    curses.wrapper(main)

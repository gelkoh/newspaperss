import os
import json
import curses


def get_json_data(path):
    abs_path = os.path.expanduser(path)

    with open(abs_path, encoding="UTF-8") as file:
        return json.load(file)


def main(stdscr):
    # Initialize curses
    curses.initscr()

    # Hide the cursor
    curses.curs_set(0)

    stdscr_num_of_lines, stdscr_num_of_cols = stdscr.getmaxyx()

    feeds = get_json_data("~/.newspaperss/feeds.json")
    num_of_feeds = len(feeds)

    title_win = curses.newwin(1, stdscr_num_of_cols, 0, 0)
    title_win.addstr(0, 0, "Newspaperss v0.1")
    title_win.refresh()

    feed_win = curses.newpad(num_of_feeds, stdscr_num_of_cols)
    for idx, feed in enumerate(feeds):
        feed_title = feed["title"]
        feed_win.addstr(idx, 0, str(idx + 1))
        feed_win.addstr(idx, 5, feed_title)
    selected_feed = 0
    feed_win_offset = 0
    feed_win.chgat(selected_feed, 0, -1, curses.A_REVERSE)
    feed_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)

    while True:
        key = stdscr.getch()

        if key == ord("q"):
            break

        if key == ord("k"):
            if selected_feed > 0:
                selected_feed -= 1

                if feed_win_offset > 0 and selected_feed == feed_win_offset - 1:
                    feed_win_offset -= 1

        if key == ord("j"):
            if selected_feed < num_of_feeds - 1:
                selected_feed += 1

                if selected_feed >= stdscr_num_of_lines - 1 + feed_win_offset:
                    feed_win_offset += 1

        feed_win.erase()
        for idx, feed in enumerate(feeds):
            feed_title = feed["title"]
            feed_win.addstr(idx, 0, str(idx + 1))
            feed_win.addstr(idx, 5, feed_title)
        feed_win.chgat(selected_feed, 0, -1, curses.A_REVERSE)

        feed_win.refresh(
            feed_win_offset,
            0,
            1,
            0,
            stdscr_num_of_lines - 1,
            stdscr_num_of_cols
        )


if __name__ == "__main__":
    curses.wrapper(main)

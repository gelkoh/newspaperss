import curses

def main(stdscr):
    # Initialize curses
    curses.initscr()

    # Hide the cursor
    curses.curs_set(0)

    stdscr_num_of_lines, stdscr_num_of_cols = stdscr.getmaxyx()
    num_of_feeds = 10

    title_win = curses.newwin(1, stdscr_num_of_cols, 0, 0)
    title_win.addstr(0, 0, "Newspaperss v0.1")
    title_win.refresh()

    feed_win = curses.newpad(num_of_feeds, stdscr_num_of_cols)
    for x in range(num_of_feeds):
        feed_win.addstr(x, 0, f"Feed {x + 1}")
    feed_win.refresh(0, 0, 1, 0, stdscr_num_of_lines - 1, stdscr_num_of_cols)

    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)

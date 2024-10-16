import curses

def create_title_win(num_of_cols):
    title_bar = curses.newwin(1, num_of_cols, 0, 0)
    title_bar.addstr(0, 0, "Newspaperss v0.1")
    title_bar.refresh()


def create_feed_win(num_of_feeds, num_of_lines, num_of_cols):
    feed_win = curses.newpad(num_of_feeds, num_of_cols)

    for x in range(num_of_feeds):
        feed_win.addstr(x, 0, f"Feed {x + 1}")

    feed_win.refresh(0, 0, 1, 0, num_of_lines, num_of_cols)


def main(stdscr):
    # Initialize curses
    curses.initscr()

    # Hide the cursor
    curses.curs_set(0)

    stdscr_num_of_lines, stdscr_num_of_cols = stdscr.getmaxyx()

    # Create windows
    create_title_win(stdscr_num_of_cols)
    create_feed_win(10, stdscr_num_of_lines - 1, stdscr_num_of_cols)

    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)

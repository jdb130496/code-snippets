#include <ncurses.h>

int main() {
    initscr(); // Initialize the window
    printw("Hello, World!"); // Print Hello, World
    refresh(); // Print it on the real screen
    getch(); // Wait for user input
    endwin(); // End curses mode

    return 0;
}
//Compilation - Powershell: g++ -o ncurses_test ncurses_test.cpp -ID:\Programs\mingw64\include\ncursesw -DNCURSES_STATIC -lncursesw

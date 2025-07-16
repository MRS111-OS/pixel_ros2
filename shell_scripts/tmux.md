# Tmux Command Guide for Attaching and Interacting with a Service's Session

## Table of Contents

- [Attaching to an Existing Session](#attaching-to-an-existing-session)
- [Navigating tmux](#navigating-tmux)
- [Interacting with the Running Terminals](#interacting-with-the-running-terminals)
- [Managing tmux Sessions](#managing-tmux-sessions)
- [Additional tmux Tips](#additional-tmux-tips)

## Attaching to an Existing Session

### 1. **List all tmux sessions**
To see the available `tmux` sessions that are running:

```bash
tmux ls
```

This will display a list of all active `tmux` sessions.

### 2. **Attach to a specific tmux session**
To attach to an existing session (e.g., `AMR`):

```bash
tmux attach-session -t AMR
```

This command will attach to the specified session, allowing you to interact with the tmux terminal and see any running commands or output.

### 3. **Attach to the most recent tmux session**
If you don’t know the session name or just want to attach to the most recently used session:

```bash
tmux attach-session
```

If only one session exists, this will automatically attach to it.

## Navigating tmux

Once attached to a tmux session, you can navigate through different windows and panes using **keyboard shortcuts**:

### 1. **List windows within the tmux session**
To see the list of windows (tabs) in your tmux session, use the **keyboard shortcut**:

- `Ctrl-b w`

This will show the available windows, each with an index number and name.

### 2. **Switch to a different window**
To switch to a different window (e.g., window 1):

- **Keyboard Shortcut**: `Ctrl-b` followed by the **window number** (e.g., `Ctrl-b 1`)

You can also switch to the next or previous window:

- **Next window**: `Ctrl-b n`
- **Previous window**: `Ctrl-b p`

### 3. **Create a new window**
If you need to create a new window in the tmux session:

- **Keyboard Shortcut**: `Ctrl-b c`

### 4. **Split the window into panes**
To split your tmux window into multiple panes (horizontal or vertical):

- **Vertical split**: `Ctrl-b %`
- **Horizontal split**: `Ctrl-b "`

You can navigate between panes using:

- **Move between panes**: `Ctrl-b` followed by the **arrow keys**

### 5. **Resize tmux panes**
To resize panes, use:

- **Resize up**: `Ctrl-b` followed by **hold** `Alt` (or `Option` key) and **arrow key**
- **Resize down**: `Ctrl-b` followed by **hold** `Alt` (or `Option` key) and **arrow key**
- **Resize left**: `Ctrl-b` followed by **hold** `Alt` (or `Option` key) and **arrow key**
- **Resize right**: `Ctrl-b` followed by **hold** `Alt` (or `Option` key) and **arrow key**

## Interacting with the Running Terminals

Once you're attached to the tmux session, you can interact with running processes:

### 1. **Send input to a specific pane**
To send input to a specific pane:

- **Move between panes**: `Ctrl-b` followed by the **arrow keys**
- Type your input or interact with the running process in the selected pane.

### 2. **Detach from the tmux session**
To detach from the tmux session and leave the processes running:

- **Keyboard Shortcut**: `Ctrl-b d`

This will detach you from the tmux session, but all running processes will continue in the background.

### 3. **Kill a pane or window**
If you want to kill a specific pane or window:

- **Kill a pane**: `Ctrl-b x` (Confirm kill)
- **Kill a window**: `Ctrl-b &` (Confirm kill)

## Additional tmux Tips

### 1. **Scrollback mode**
To scroll back in the terminal to view previous output in a pane, press:

- **Keyboard Shortcut**: `Ctrl-b [`

Use the **arrow keys** to scroll up and down. To exit scrollback mode, press `q`.

### 2. **Save tmux output to a file**
You can capture the output from a pane and save it to a file by using:

- **Keyboard Shortcut**: `Ctrl-b :pipe-pane 'cat > /path/to/file.txt'`

This will save the pane’s output to the specified file.

### 3. **Show tmux status**
To toggle the tmux status bar (the bar at the bottom of the terminal that shows session and window information), use:

- **Keyboard Shortcut**: `Ctrl-b t`

### 4. **Enable mouse mode**
If you prefer using the mouse to select windows or scroll through panes, enable mouse mode:

```bash
tmux set -g mouse on
```

You can then use the mouse to interact with the tmux panes.

## Note

For more advanced tmux usage, check out the official tmux man pages or [online documentation](https://man7.org/linux/man-pages/man1/tmux.1.html).

For quick ref: [tmuxcheetsheet.com](https://tmuxcheatsheet.com/)
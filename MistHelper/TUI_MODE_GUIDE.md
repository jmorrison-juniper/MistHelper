# MistHelper TUI Mode Guide

## Overview
MistHelper now includes a Terminal User Interface (TUI) mode that provides a visual, keyboard-driven way to navigate and execute Mist API operations. This mode complements the traditional menu-driven interface by organizing operations into logical categories.

## Launch TUI Mode
```bash
python MistHelper.py --tui
```

## Features

### Visual Organization
Operations are automatically organized into logical categories:

- **System** - Exit and core functions
- **Sites** - Site-level operations and exports
- **Devices** - Device inventory, stats, and management
- **Statistics** - Metrics, stats, and analytics
- **Templates** - Gateway, AP, network, RF, switch templates
- **Clients** - Wireless and wired client data
- **Security** - Alarms, rogue devices, security events
- **Configuration** - Licenses, PSKs, webhooks, WLANs
- **Insights** - SLE metrics and Marvis AI
- **WebSocket Commands** - Real-time device commands
- **Packet Captures** - Site and org-level captures
- **Advanced** - Specialized operations
- **DESTRUCTIVE** - Operations requiring explicit confirmation (color-coded red)

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `↑` `↓` | Move up/down within current category |
| `←` `→` | Switch between categories |
| `Enter` | Execute selected operation |
| `Q` or `Esc` | Exit TUI mode |

### Visual Indicators

- **Green highlight** - Currently selected item
- **Bold green on black** - Current category
- **Red text** - DESTRUCTIVE operations (use with caution)
- **White text** - Standard operations
- **Cyan borders** - Category and item panels

## Cross-Platform Support

The TUI mode automatically detects the platform and uses the appropriate keyboard input method:

- **Windows**: Uses `msvcrt` for keyboard detection
- **Linux/Unix**: Uses `select` for non-blocking input
- **SSH Compatible**: Works over remote SSH sessions

## Layout Design

```
╭─────────────────── MistHelper TUI - Mist API Navigator ───────────────────╮
│                                                                           │
│  ╭─── Categories ───╮  ╭────────────── [Category Name] ──────────────╮  │
│  │                  │  │                                               │  │
│  │   > System       │  │  #   Description                             │  │
│  │     Sites        │  │  ──────────────────────────────────────────  │  │
│  │     Devices      │  │  11  > Export all sites in organization      │  │
│  │     Statistics   │  │  12    Export device inventory               │  │
│  │     ...          │  │  13    Export device statistics              │  │
│  │                  │  │  ...                                          │  │
│  ╰──────────────────╯  ╰───────────────────────────────────────────────╯  │
│                                                                           │
│  Navigation: ↑↓ Move  ←→ Category  Enter Execute  Q/Esc Quit             │
╰───────────────────────────────────────────────────────────────────────────╯
```

## Operation Execution

When you press `Enter` on a selected operation:

1. **Screen clears** - Provides clean view of operation output
2. **Operation executes** - Runs the selected function with full output
3. **Status display** - Shows `[COMPLETE]`, `[INTERRUPTED]`, or `[ERROR]`
4. **Wait for input** - Press any key to return to TUI menu
5. **Menu restores** - Returns to exact position you left

## Benefits Over Traditional Menu

| Traditional Menu | TUI Mode |
|-----------------|----------|
| Remember menu numbers | Visual browsing by category |
| Linear list (100+ options) | Organized into 12 categories |
| Text-only navigation | Color-coded visual interface |
| One-time execution | Persistent navigation session |
| Requires typing numbers | Arrow key navigation |

## Design Philosophy

The TUI mode follows MistHelper's core principles:

- **Safety-First**: DESTRUCTIVE operations clearly marked in red
- **Non-Intrusive**: Does not modify existing codebase, only additions
- **SSH-Compatible**: Works over remote connections
- **Professional**: Clear, organized, business-appropriate interface
- **Accessible**: No technical jargon, intuitive navigation

## Technical Implementation

- **Framework**: Rich library for terminal rendering
- **Architecture**: MistHelperTUI class (lines ~27825-28165)
- **Integration**: `--tui` flag added to argument parser
- **Organization**: `_organize_menu_into_categories()` method auto-categorizes all menu_actions
- **Keyboard**: Cross-platform input handling with fallback support

## Future Enhancement Opportunities

Potential areas for guided development:

1. **Search/Filter** - Type to filter operations by keyword
2. **Favorites** - Mark frequently-used operations
3. **History** - Show recently executed operations
4. **Details View** - Preview operation requirements before execution
5. **Multi-execute** - Queue multiple operations
6. **Status Bar** - Show org_id, current mode, connection status
7. **Help Panel** - Context-sensitive help for selected operation
8. **Themes** - Color scheme customization

## Usage Examples

### Quick Site Export
```bash
# Launch TUI
python MistHelper.py --tui

# Navigation:
# 1. Press → to move to "Sites" category
# 2. Press ↓ to select "Export all sites"
# 3. Press Enter to execute
# 4. Wait for completion
# 5. Press any key to return
# 6. Press Q to exit
```

### Browse API Capabilities
```bash
# Launch TUI and explore categories
python MistHelper.py --tui

# Use ← → to browse all categories
# Use ↑ ↓ to review available operations
# Press Q when done exploring
```

### Safe Learning Mode
The TUI makes it easy to explore without risk:
- DESTRUCTIVE operations are clearly marked in red
- All operations require explicit execution (Enter key)
- Can browse safely without triggering anything
- Perfect for learning the API capabilities

## Notes

- TUI mode requires the Rich library (auto-installed by MistHelper)
- All operations execute with same functionality as traditional menu
- Organization context (org_id) follows standard MistHelper flow
- Works in containers and SSH sessions
- Logging continues to `data/script.log` as normal
- Exit with Q or Esc returns control to terminal cleanly

---

**Version**: 25.10.21.09.21 (TUI Mode Initial Release)  
**Author**: MistHelper Development Team  
**Status**: Production Ready - Core Navigation Complete

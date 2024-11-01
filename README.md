# ZiggleScript Documentation

ZiggleScript is a simple command-based scripting language for creating graphical shapes and text on a coordinate system.

## Available Commands

### 1. Create Rectangle

*   **Syntax**: `CREATE RECTANGLE x1 x2 y1 y2 color options<>`
*   **Parameters**:
    *   `x1`, `x2`: Horizontal coordinates (float) defining the left and right edges.
    *   `y1`, `y2`: Vertical coordinates (float) defining the bottom and top edges.
    *   `color`: Color string (e.g., "lightblue").
    *   `options`: Optional; "FILLED" for filled rectangles.
*   **Example**: `CREATE RECTANGLE 10 90 10 60 lightblue FILLED<>`

### 2. Create Line

*   **Syntax**: `CREATE LINE x1 y1 x2 y2 color<>`
*   **Parameters**:
    *   `x1`, `y1`: Starting coordinates (float).
    *   `x2`, `y2`: Ending coordinates (float).
    *   `color`: Color string.
*   **Example**: `CREATE LINE 10 60 90 60 black<>`

### 3. Create Text

*   **Syntax**: `CREATE TEXT x1 x2 y1 y2 "text" color font_size<>`
*   **Parameters**:
    *   `x1`, `x2`: Horizontal coordinates (float) defining the text area.
    *   `y1`, `y2`: Vertical coordinates (float) defining the text area.
    *   `"text"`: Displayed text string (enclosed in quotes).
    *   `color`: Optional color string (default: "black").
    *   `font_size`: Optional integer for font size adjustment.
*   **Example**: `CREATE TEXT 20 80 50 50 "Welcome To Ziggle" darkblue 20<>`

## Usage Notes

*   Commands must end with `< >`.
*   Color values can be common names (e.g., "red") or hex codes.
*   Multiple commands can be combined in one line.

## Example Usage

```sql
CREATE RECTANGLE 10 90 10 60 lightblue FILLED<> 
CREATE LINE 10 60 90 60 black<> 
CREATE TEXT 20 80 50 50 "Hello World" darkblue 20<>
Contributing and Support
```
Contribute to ZiggleScript's growth by sharing designs, reporting issues or suggesting enhancements.

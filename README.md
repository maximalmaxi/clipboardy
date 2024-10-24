# Clipboardy

Clipboardy is a user-friendly clipboard management application that allows you to save, organize, and encrypt your clipboard clips. With features like auto-saving, clipboard monitoring, and support for various content types, Clipboardy enhances your clipboard experience.

## Features

- **Secure Storage**: Encrypts your clipboard content for privacy using cryptography.
- **Auto-Save Feature**: Automatically saves new clipboard entries.
- **Content Type Detection**: Identifies URLs, emails, IP addresses, credit card numbers, and plain text for easy filtering.
- **User-Friendly UI**: Built with CustomTkinter for a modern look and feel.
- **Manage Clips**: Easily copy, delete, or view your saved clips.
- **Cross-Platform**: Works on any platform that supports Python.

## Requirements

Before you begin, ensure you have met the following requirements:

- **Python 3.x**
- Required libraries (install with `pip install -r requirements.txt`):
  - `pyperclip`
  - `cryptography`
  - `validators`
  - `customtkinter`

## Installation

### Use releases for easy download or:

1. **Clone the Repository**:
```bash
  git clone https://github.com/clipboardy/clipboardy.git
  cd clipboardy
```
2. **Install Dependencies**
```bash
  pip install -r requirements.txt
```
3. **Run the Application**
```bash
  python clipui.py
```
## Contributing

If you'd like to contribute to Clipboardy, please fork the repository and submit a pull request.

## Acknowledgements

 - [pyperclip for clipboard access](https://pypi.org/project/pyperclip/)
 - [validators for content type validation](https://pypi.org/project/validators/)
 - [cryptography for encryption and decryption](https://pypi.org/project/cryptography/)
 - [customtkinter for a modern UI](https://github.com/TomSchimansky/CustomTkinter)
## License

[MIT](https://choosealicense.com/licenses/mit/)


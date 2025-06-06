# Troubleshooting & FAQ

## Common Issues

### Q: The app won't start or crashes on launch.
- **A:** Ensure you are using Python 3.8+ and have activated the correct virtual environment. Check that all dependencies are installed (`pip install -r requirements.txt`).

### Q: Collectors fail with authentication errors.
- **A:** Double-check your API keys in the Configuration tab or `.env` file.

### Q: UI looks broken or styles are missing.
- **A:** Make sure the QSS files are present in `app/resources/styles/` and that you are not running in a restricted environment.

### Q: Sound notifications don't work.
- **A:** Ensure your system audio is enabled and the required `.wav` files are present in `app/resources/audio/`.

### Q: Batch operations are slow or freeze.
- **A:** Make sure you are not running out of memory. Large operations are threaded, but very large corpora may require more RAM.

### Q: How do I reset the app to defaults?
- **A:** Delete or rename the `theme_config.json` and configuration files in your app directory.

---

## FAQ

**Q: Can I add my own data sources?**  
A: Yes! See the [Developer Guide](./DEVELOPER_GUIDE.md) for instructions on adding new collectors.

**Q: How do I export my corpus?**  
A: Use the export feature in the Corpus Manager or manually copy the corpus directory.

**Q: Where are logs stored?**  
A: In `~/.cryptofinance/logs/` by default.

**Q: How do I get support?**  
A: Use GitHub Issues or contact support@yourcompany.com.

---

If your issue is not listed, please check the logs and contact support.

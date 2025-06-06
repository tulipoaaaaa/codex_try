# Admin Guide: CryptoFinance Corpus Builder

## Table of Contents

1. Installation & Setup
2. Configuration
3. Upgrades & Maintenance
4. Backup & Restore
5. Logging & Monitoring
6. Security

---

## Installation & Setup

- See [README.md](./README.md#quickstart) for prerequisites and installation steps.
- Use the provided `requirements.txt` and `launch_app.bat` for setup.

---

## Configuration

- **API Keys**: Store securely in the Configuration tab or `.env` file.
- **Directories**: Set up corpus, raw, processed, and log directories.
- **Environment**: Switch between test, master, and production as needed.

---

## Upgrades & Maintenance

- Pull latest code from the repository.
- Run `pip install -r requirements.txt` to update dependencies.
- Review the [CHANGELOG.md](./CHANGELOG.md) for breaking changes.

---

## Backup & Restore

- Regularly back up the `corpus` and `logs` directories.
- Use the export/import features in the Corpus Manager for data migration.

---

## Logging & Monitoring

- Logs are stored in `~/.cryptofinance/logs/`.
- Use the Logs tab for real-time monitoring and export.

---

## Security

- Store API keys securely.
- Limit access to sensitive directories.
- Regularly update dependencies to patch vulnerabilities.

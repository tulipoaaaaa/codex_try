+-------------------+ +-------------------+ +-------------------+
| Collectors | ---> | Processors | ---> | Corpus Manager |
| (ISDA, GitHub, | | (PDF, Text, etc.) | | (File/Meta Mgmt) |
| Anna's, etc.) | +-------------------+ +-------------------+
+-------------------+ | |
| | |
v v v
+---------------------------------------------------------------+
| Main Application (PyQt6 UI) |
| +-------------------+ +-------------------+ +----------+ |
| | Balancer | | Analytics | | Logs | |
| +-------------------+ +-------------------+ +----------+ |
| | | | |
| v v v |
| ProjectConfig <------------------------------------------+ |
+---------------------------------------------------------------+


- **Collectors**: Gather data from multiple sources.
- **Processors**: Clean, extract, and analyze documents.
- **Corpus Manager**: Organizes files, metadata, and supports batch ops.
- **Balancer**: Ensures domain distribution matches targets.
- **Analytics**: Provides insights and trends.
- **Logs**: Real-time monitoring and error tracking.
- **ProjectConfig**: Centralized configuration and environment management.

---

## Data Flow

1. **Collection** → **Processing** → **Corpus Management** → **Analysis/Balance**
2. All components communicate via Qt signals/slots for loose coupling.

---

## Threading Model

- All long-running operations run in `QThread` workers.
- UI remains responsive; progress and status are updated via signals.

---

## Extensibility

- New collectors/processors can be added by subclassing and registering in the factory.
- UI is modular; new tabs/widgets can be added easily.

---

## Security

- API keys and sensitive data are stored securely.
- User data is never sent externally unless explicitly exported.

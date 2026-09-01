# Security policy

## Reporting a vulnerability

Please do not report security vulnerabilities in public issues. Instead, open a private GitHub security advisory for this repository or contact the maintainers through the repository's private security-reporting channel once enabled.

Include a clear description, reproduction steps, impact assessment, and any proof of concept. We will acknowledge receipt, investigate, and coordinate a fix before public disclosure.

## Deployment guidance

API Test Platform can inspect repositories and execute test-related commands. Deploy it with least privilege:

- restrict `BACKEND_ROOT_DIR` to a dedicated workspace;
- enable `BACKEND_VIRTUAL_MODE=true` for untrusted code;
- never expose provider keys in browser-visible variables;
- use isolated infrastructure and network policies for targets under test;
- rotate keys immediately if they are exposed.

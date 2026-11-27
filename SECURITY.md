# Security

This tool runs on your machine. Notes and uploads are not sent to a service and no API key is needed.

Uploads are checked by extension, magic bytes and size before they are read fully. CORS is limited to local origins. Set `EXAM_ALLOWED_ORIGINS` if you serve the page from another host.

Rendered note text is escaped before it reaches HTML. If you find a way around that, report it privately.

Report security problems through GitHub's reporting channel or message the repository owner. Do not paste private documents into a public issue.

# Privacy

## What this app does
- Resume and job-posting text (pasted or extracted from an uploaded PDF) is held in Streamlit session memory only and is used to compute results for your session.
- The app code does not log that text, does not write it to disk, and does not send it to any third-party service. Error messages for bad input never include document content.
- PDFs are parsed in memory (size, page and text-length limits apply). Nothing is saved by the app.
- Streamlit usage statistics collection is disabled in `.streamlit/config.toml`.

## What it cannot control
- The hosting platform (for example Streamlit Community Cloud) runs its own infrastructure, request handling and logs, and may retain metadata or traffic records. Check the host's privacy policy.
- Your browser, network and any other tools you use alongside the app.

Do not upload documents you are not comfortable processing on the hosting platform.

# airpress

Airpress is an App Engine-based asset management and documentation system that
integrates with Google Drive. Manage your assets, content, and documentation
in Google Drive and sync them to Airpress to get a beautiful, branded
asset and documentation repository.

Airpress provides some lightweight digital asset management system features
such as an access request flow, approval system, and tracks which assets are
the most frequently downloaded.

## Setup

```
# Generate service account key
openssl pkcs12 -in *.p12 -out key.pem -nocerts -nodes
```

## Enable Drive API

https://cloud.console.google.com/apis/api/drive/overview

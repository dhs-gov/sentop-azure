# To use this configuration file, rename this file as 'sentop_config.py'.


# PostgreSQL configuration
database = {
      "url": "127.0.0.1",
      "database": "mydatabase",
      "username": "username",
      "password": "password"
}

# Results generation. Here, JSON results are provided in the HTTP query
# response.
results = {
      "database": True,
      "json": True,
      "excel": True
}
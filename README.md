# Yelp Crawler

The purpose is to develop a Yelp crawler that scraps all the businesses from Yelp website.
The yelp_data.json has only 10 entries as an example.

The script parses only the first page of a specific business by default.
To increase the number of the pages to parse please update ```self.limit_pages``` 
in the ```__init__``` method

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirement libraries.

```bash
pip install -r requirements.txt
```

## Usage
```python
# Run the script to get the result in yelp_data.json
python main.py --category 'contractors' --location 'San Francisco, CA'
```

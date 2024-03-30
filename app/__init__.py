import json
import logging
import requests
import requests_cache

from flask import (Flask, make_response, redirect, render_template, request,
                   url_for)

CONFIG_FILE = "./config.json"

app = Flask(__name__)

SESSION = requests.Session()

app.config.from_file(CONFIG_FILE, load=json.load)
SESSION.headers.update({'Authorization': app.config["API_KEY"]})
logging.basicConfig(level=logging.DEBUG)
requests_cache.install_cache(**app.config["CACHE_DATA"])

def build_default_page():
    return (url_for(
    'category',
    category=app.config["VARIOUS"]["CATEGORIES"][0],
    page=1
))

@app.route('/', methods=['GET', 'POST'])
def root():
    ''' Base URL redirect to the first page of general category. '''
    return (redirect(build_default_page()))


@app.errorhandler(404)
def page_not_found(error):
    ''' Not existing pages redirect to the first page of general category. '''
    return (redirect(build_default_page()))


@app.route('/category/<string:category>', methods=['GET', 'POST'])
def category(category):
    ''' Handles category route.

    Parameters:
        - name: category
          in: path
          description: Name of the news category
        - name: page
          in: query
          description: Number of the page
    '''
    page = request.args.get('page', default=1, type=int)
    if page < 1:
        return redirect(url_for('category', category=category, page=1))
    if request.method == 'POST' and category in app.config["VARIOUS"]["CATEGORIES"]:
        return do_post(page, category)
    if category in app.config["VARIOUS"]["CATEGORIES"]:
        params = {'page': page, 'category': category, 'pageSize': app.config["VARIOUS"]["PAGE_SIZE"]}
        country = get_cookie('country')
        if country is not None:
            params.update({'country': country})
        response = SESSION.get(app.config["ENDPOINTS"]["TOP_HEADLINES"], params=params)
        if response.status_code == 200:
            pages = count_pages(response.json())
            if page > pages:
                page = pages
                return redirect(
                    url_for('category', category=category, page=page))
            articles = parse_articles(response.json())
            theme = get_cookie('theme') if get_cookie(
                'theme') is not None else 'light'
            return render(articles, page, pages, country, category, theme)
        elif response.status_code == 401:
            return render_template(app.config['VARIOUS']['401_TEMPLATE'])
    return redirect(url_for('category', category='general', page=page))


@app.route('/search/<string:query>', methods=['GET', 'POST'])
def search(query: str):
    ''' Handles category route.

    Parameters:
        - name: query
          in: path
          description: Query string to be searched
        - name: page
          in: query
          description: Number of the page
    '''
    page = request.args.get('page', default=1, type=int)
    if page < 1:
        return redirect(url_for('search', query=query, page=1))
    params = {
        'qInTitle': query,
        'sortBy': 'relevancy',
        'page': page,
        'pageSize': app.config["VARIOUS"]["PAGE_SIZE"]
    }
    if request.method == 'POST':
        return do_post(page, category='search', current_query=query)
    response = SESSION.get(app.config["ENDPOINTS"]["EVERYTHING"], params=params)
    pages = count_pages(response.json())
    if page > pages:
        page = pages
        return redirect(url_for('search', query=query, page=page))
    articles = parse_articles(response.json())
    return render(articles,
                  page,
                  pages,
                  country=get_cookie('country'),
                  category='search',
                  theme=get_cookie('theme'))


def do_post(page=1, category='general', current_query=None):
    ''' Helper method that handles POST request basing on the input. '''
    new_query = request.form.get('search_query')
    country = request.form.get('country')
    theme = request.form.get('theme')
    next_page = request.form.get('next_page')
    previous_page = request.form.get('previous_page')
    if new_query is not None and new_query != '':
        return redirect(url_for('search', query=new_query, page=1))
    if country is not None and country != get_cookie('country'):
        response = make_response(
            redirect(url_for('category', category=category, page=1)))
        response.set_cookie('country', country)
        return response
    if theme is not None:
        response = make_response(
            redirect(url_for('category', category=category, page=page)))
        response.set_cookie('theme', theme)
        return response
    if next_page is not None:
        page = int(next_page) + 1
    elif previous_page is not None:
        page = int(previous_page) - 1
    if category == 'search':
        return redirect(url_for('search', query=current_query, page=page))
    return redirect(url_for('category', category=category, page=page))


def parse_articles(response: dict) -> list:
    ''' Parses articles fetched from News API.

    Returns:
        A list of dicts containing publishing title and URL.
    '''
    parsed_articles = []
    if response.get('status') == 'ok':
        for article in response.get('articles'):
            parsed_articles.append({
                'title': article['title'],
                'url': article['url']
            })
    return parsed_articles


def count_pages(response: dict) -> int:
    ''' Helper method that counts number of total pages basing on total
        results from News API response and PAGE_SIZE.

    Returns:
        An int with a number of total pages. '''
    if response.get('status') == 'ok':
        return (-(-response.get('totalResults', 0) // app.config["VARIOUS"]["PAGE_SIZE"]))
    return 0


def render(articles, page, pages, country, category, theme):
    ''' Renders the template with appropriate variables. Up to 12 pages
        allowed. '''
    pages = pages if pages <= 12 else 12
    return render_template(app.config['VARIOUS']['TEMPLATE'],
                           categories=app.config["VARIOUS"]["CATEGORIES"],
                           countries=app.config["VARIOUS"]["COUNTRIES"],
                           **vars())


def get_cookie(key):
    """Get a cookie's value."""
    return request.cookies.get(key)


if __name__ == '__main__':
    app.run()
def get_stock_historical_data(
    stock,
    country,
    from_date,
    to_date,
    as_json=False,
    order="ascending",
    interval="Daily",
):
    """
    This function retrieves historical data from the introduced stock from Investing.com. So on, the historical data
    of the introduced stock from the specified country in the specified date range will be retrieved and returned as
    a :obj:`pandas.DataFrame` if the parameters are valid and the request to Investing.com succeeds. Note that additionally
    some optional parameters can be specified: as_json and order, which let the user decide if the data is going to
    be returned as a :obj:`json` or not, and if the historical data is going to be ordered ascending or descending (where the
    index is the date), respectively.

    Args:
        stock (:obj:`str`): symbol of the stock to retrieve historical data from.
        country (:obj:`str`): name of the country from where the stock is.
        from_date (:obj:`str`): date formatted as `dd/mm/yyyy`, since when data is going to be retrieved.
        to_date (:obj:`str`): date formatted as `dd/mm/yyyy`, until when data is going to be retrieved.
        as_json (:obj:`bool`, optional):
            to determine the format of the output data, either a :obj:`pandas.DataFrame` if False and a :obj:`json` if True.
        order (:obj:`str`, optional): to define the order of the retrieved data which can either be ascending or descending.
        interval (:obj:`str`, optional):
            value to define the historical data interval to retrieve, by default `Daily`, but it can also be `Weekly` or `Monthly`.

    Returns:
        :obj:`pandas.DataFrame` or :obj:`json`:
            The function can return either a :obj:`pandas.DataFrame` or a :obj:`json` object, containing the retrieved
            historical data of the specified stock from the specified country. So on, the resulting dataframe contains the
            open, high, low, close and volume values for the selected stock on market days and the currency in which those
            values are presented.

            The returned data is case we use default arguments will look like::

                Date || Open | High | Low | Close | Volume | Currency
                -----||------|------|-----|-------|--------|----------
                xxxx || xxxx | xxxx | xxx | xxxxx | xxxxxx | xxxxxxxx

            but if we define `as_json=True`, then the output will be::

                {
                    name: name,
                    historical: [
                        {
                            date: 'dd/mm/yyyy',
                            open: x,
                            high: x,
                            low: x,
                            close: x,
                            volume: x,
                            currency: x
                        },
                        ...
                    ]
                }

    Raises:
        ValueError: raised whenever any of the introduced arguments is not valid or errored.
        IOError: raised if stocks object/file was not found or unable to retrieve.
        RuntimeError: raised if the introduced stock/country was not found or did not match any of the existing ones.
        ConnectionError: raised if connection to Investing.com could not be established.
        IndexError: raised if stock historical data was unavailable or not found in Investing.com.

    Examples:
        >>> data = investpy.get_stock_historical_data(stock='bbva', country='spain', from_date='01/01/2010', to_date='01/01/2019')
        >>> data.head()
                     Open   High    Low  Close  Volume Currency
        Date
        2010-01-04  12.73  12.96  12.73  12.96       0      EUR
        2010-01-05  13.00  13.11  12.97  13.09       0      EUR
        2010-01-06  13.03  13.17  13.02  13.12       0      EUR
        2010-01-07  13.02  13.11  12.93  13.05       0      EUR
        2010-01-08  13.12  13.22  13.04  13.18       0      EUR

    """

    if not stock:
        raise ValueError(
            "ERR#0013: stock parameter is mandatory and must be a valid stock symbol."
        )

    if not isinstance(stock, str):
        raise ValueError("ERR#0027: stock argument needs to be a str.")

    if country is None:
        raise ValueError("ERR#0039: country can not be None, it should be a str.")

    if country is not None and not isinstance(country, str):
        raise ValueError("ERR#0025: specified country value not valid.")

    if not isinstance(as_json, bool):
        raise ValueError(
            "ERR#0002: as_json argument can just be True or False, bool type."
        )

    if order not in ["ascending", "asc", "descending", "desc"]:
        raise ValueError(
            "ERR#0003: order argument can just be ascending (asc) or descending (desc),"
            " str type."
        )

    if not interval:
        raise ValueError(
            "ERR#0073: interval value should be a str type and it can just be either"
            " 'Daily', 'Weekly' or 'Monthly'."
        )

    if not isinstance(interval, str):
        raise ValueError(
            "ERR#0073: interval value should be a str type and it can just be either"
            " 'Daily', 'Weekly' or 'Monthly'."
        )

    interval = interval.lower()

    if interval not in ["daily", "weekly", "monthly"]:
        raise ValueError(
            "ERR#0073: interval value should be a str type and it can just be either"
            " 'Daily', 'Weekly' or 'Monthly'."
        )

    try:
        datetime.strptime(from_date, "%d/%m/%Y")
    except ValueError:
        raise ValueError(
            "ERR#0011: incorrect from_date date format, it should be 'dd/mm/yyyy'."
        )

    try:
        datetime.strptime(to_date, "%d/%m/%Y")
    except ValueError:
        raise ValueError(
            "ERR#0012: incorrect to_date format, it should be 'dd/mm/yyyy'."
        )

    start_date = datetime.strptime(from_date, "%d/%m/%Y")
    end_date = datetime.strptime(to_date, "%d/%m/%Y")

    if start_date >= end_date:
        raise ValueError(
            "ERR#0032: to_date should be greater than from_date, both formatted as"
            " 'dd/mm/yyyy'."
        )

    resource_package = "investpy"
    resource_path = "/".join((("resources", "stocks.csv")))
    if pkg_resources.resource_exists(resource_package, resource_path):
        stocks = pd.read_csv(
            pkg_resources.resource_filename(resource_package, resource_path),
            keep_default_na=False,
        )
    else:
        raise FileNotFoundError("ERR#0056: stocks file not found or errored.")

    if stocks is None:
        raise IOError("ERR#0001: stocks object not found or unable to retrieve.")

    country = unidecode(country.strip().lower())

    if country not in get_stock_countries():
        raise RuntimeError(
            "ERR#0034: country "
            + country.lower()
            + " not found, check if it is correct."
        )

    stocks = stocks[stocks["country"] == country]

    stock = unidecode(stock.strip().lower())

    if stock not in list(stocks["symbol"].apply(unidecode).str.lower()):
        raise RuntimeError(
            "ERR#0018: stock " + stock + " not found, check if it is correct."
        )

    symbol = stocks.loc[
        (stocks["symbol"].apply(unidecode).str.lower() == stock).idxmax(), "symbol"
    ]
    id_ = stocks.loc[
        (stocks["symbol"].apply(unidecode).str.lower() == stock).idxmax(), "id"
    ]
    name = stocks.loc[
        (stocks["symbol"].apply(unidecode).str.lower() == stock).idxmax(), "name"
    ]

    stock_currency = stocks.loc[
        (stocks["symbol"].apply(unidecode).str.lower() == stock).idxmax(), "currency"
    ]

    params = {
        "start-date": start_date.strftime("%Y-%m-%d"),
        "end-date": end_date.strftime("%Y-%m-%d"),
        "time-frame": interval.capitalize(),
        "add-missing-rows": "false",
    }

    headers = {
        "User-Agent": random_user_agent(),
        "X-Requested-With": "XMLHttpRequest",
        "Domain-Id": "www",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    url = f"https://api.investing.com/api/financialdata/historical/{id_}"

    req = requests.get(url, params=params, headers=headers)

    if req.status_code != 200:
        raise ConnectionError(
            "ERR#0015: error " + str(req.status_code) + ", try again later."
        )

    data = req.json()["data"]

    if not data:
        raise ValueError("No information available!")

    result = list()

    for entry in data:
        stock_date = datetime.strptime(
            str(
                datetime.fromtimestamp(
                    entry["rowDateRaw"], tz=pytz.timezone("GMT")
                ).date()
            ),
            "%Y-%m-%d",
        )

        stock_close = float(entry["last_closeRaw"])
        stock_open = float(entry["last_openRaw"])
        stock_high = float(entry["last_maxRaw"])
        stock_low = float(entry["last_minRaw"])

        stock_volume = entry["volumeRaw"]

        result.insert(
            len(result),
            Data(
                stock_date,
                stock_open,
                stock_high,
                stock_low,
                stock_close,
                stock_volume,
                stock_currency,
                None,
            ),
        )

    if order in ["ascending", "asc"]:
        result = result[::-1]
    elif order in ["descending", "desc"]:
        result = result

    if as_json is True:
        json_ = {
            "name": name,
            "recent": [value.stock_as_json() for value in result],
        }

        return json.dumps(json_, sort_keys=False)
    elif as_json is False:
        df = pd.DataFrame.from_records([value.stock_to_dict() for value in result])
        df.set_index("Date", inplace=True)

        return df




from chanlun_v2_app.data_fetcher import fetch_and_save


if __name__ == "__main__":
    result = fetch_and_save()
    print(f"已采集 {result['count']} 根K线，最新一根：{result['latest_dt']} @ {result['latest_close']}")


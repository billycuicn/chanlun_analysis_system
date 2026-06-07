from chanlun_v2_app.report import generate_report


if __name__ == "__main__":
    result = generate_report()
    print(f"报告已生成：{result['local_path']}")
    if result["obsidian_path"]:
        print(f"已推送至 Obsidian：{result['obsidian_path']}")


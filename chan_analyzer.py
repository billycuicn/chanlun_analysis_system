from chanlun_v2_app.analyzer import analyze_and_save


if __name__ == "__main__":
    result = analyze_and_save()
    print(result["summary"].get("message", f"已生成 {len(result['segments'])} 条线段，{len(result['zhongshu'])} 个中枢，{len(result['signals'])} 个买卖点"))


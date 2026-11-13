# Capital Bikeshare 站點營運診斷｜階段報告

以 2025 年 1 月 Capital Bikeshare 旅次與 CityBikes 歷史站況，找出值得優先調查的站點與時段，再用站況驗證具體日期的借還變化。

## 三項發現

1. **站點 ID 缺值會改變車種組成。** 一月借出 285,695 筆，起迄站 ID 皆完整的有 166,757 筆（58.37%）。只保留兩端完整旅次時，電輔車占比由 72.37% 降至 52.77%。站點分析因此分別按借出端及歸還端的站點 ID 納入事件。[缺值敏感度](notebooks/13_missingness_sensitivity.ipynb)
2. **月量相近的站點，平日早上可有相反的借還方向。** 在 20 個一般平日的 08:00–08:59，31600 和 31101 分別有 18 天和 17 天借出較多，31699 有 18 天歸還較多。站況在 31600 的 1/8、1/14 與 31101 的 1/29 記錄到零可借車，在 31699 的 1/15 記錄到零可還空位。三站各有 15 至 18 天的站況涵蓋不足。[三站對照](notebooks/15_january_station_comparison.ipynb) · [歷史站況](notebooks/16_historical_station_status.ipynb)
3. **站況時間欄位會影響庫存對帳。** 固定 31600 站況端點，改用來源更新時間切分旅次後，1/8 與 1/14 首筆零值前的短區間各多計入一筆借出，差額均由 −1 輛變為 0 輛。1/14 的較長區間觀測到可借車少了 13 輛，已記錄旅次可解釋淨減 12 輛。[時間線與時間口徑比較](notebooks/16_historical_station_status.ipynb)

## 優先核對

核對 31600 站在 **1/14 07:55:37–08:58:35** 的原始站況與調度紀錄，確認剩餘 1 輛差額。上述為華盛頓當地的站況採集時間，旅次檔暫按同一時區解讀。零可借車的持續時間與整月發生頻率需要更完整的站況紀錄。[一頁決策摘要](DECISION_SUMMARY.md)

Bike-share data by CityBikes contributors and available from [CityBikes](https://data.citybik.es).

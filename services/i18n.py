"""Centralised multi-language translation for GoushFi.

Supported languages:
    ar  – العربية (Arabic)          RTL
    en  – English                   LTR
    zh  – 中文 (Chinese Simplified)  LTR
    ko  – 한국어 (Korean)            LTR
    ja  – 日本語 (Japanese)          LTR
    id  – Bahasa Indonesia          LTR
    ms  – Bahasa Melayu (Malay/Singapore) LTR

The ``make_t`` function returns a translator with the same ``t(ar, en)``
signature used throughout the codebase.  When the active language is
Arabic or English, the original two-argument path is used directly (zero
lookup cost).  For other languages the *en* argument is used as a dict
key into the ``_TRANSLATIONS`` table; if no entry exists the English
fallback is returned.
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

# ---------------------------------------------------------------------------
# Language registry
# ---------------------------------------------------------------------------

LANGUAGES: dict[str, str] = {
    "العربية": "ar",
    "English": "en",
    "中文": "zh",
    "한국어": "ko",
    "日本語": "ja",
    "Bahasa Indonesia": "id",
    "Bahasa Melayu": "ms",
}

LANGUAGE_NAMES: list[str] = list(LANGUAGES.keys())

RTL_LANGUAGES: set[str] = {"العربية"}

# ---------------------------------------------------------------------------
# Month names per language
# ---------------------------------------------------------------------------

MONTHS: dict[str, list[str]] = {
    "ar": [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
    ],
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "zh": [
        "一月", "二月", "三月", "四月", "五月", "六月",
        "七月", "八月", "九月", "十月", "十一月", "十二月",
    ],
    "ko": [
        "1월", "2월", "3월", "4월", "5월", "6월",
        "7월", "8월", "9월", "10월", "11월", "12월",
    ],
    "ja": [
        "1月", "2月", "3月", "4月", "5月", "6月",
        "7月", "8月", "9月", "10月", "11月", "12月",
    ],
    "id": [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ],
    "ms": [
        "Januari", "Februari", "Mac", "April", "Mei", "Jun",
        "Julai", "Ogos", "September", "Oktober", "November", "Disember",
    ],
}

# ---------------------------------------------------------------------------
# Translations  {en_text: {lang_code: translated_text}}
# Arabic is never looked up here (it comes from the first t() argument).
# ---------------------------------------------------------------------------

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Navigation / pages ──────────────────────────────────────────────
    "Home": {"zh": "首页", "ko": "홈", "ja": "ホーム", "id": "Beranda", "ms": "Beranda"},
    "Account": {"zh": "账户", "ko": "계좌", "ja": "アカウント", "id": "Akun", "ms": "Akun"},
    "Settings": {"zh": "设置", "ko": "설정", "ja": "設定", "id": "Pengaturan", "ms": "Pengaturan"},
    "GoushFi Settings": {"zh": "GoushFi 设置", "ko": "GoushFi 설정", "ja": "GoushFi 設定", "id": "Pengaturan GoushFi", "ms": "Pengaturan GoushFi"},
    "Dashboard Card Visibility": {"zh": "仪表板卡片可见性", "ko": "대시보드 카드 표시", "ja": "ダッシュボードカード表示", "id": "Visibilitas Kartu Dashboard", "ms": "Visibilitas Kartu Dashboard"},
    "Projects": {"zh": "项目", "ko": "프로젝트", "ja": "プロジェクト", "id": "Proyek", "ms": "Proyek"},
    "Savings": {"zh": "储蓄", "ko": "저축", "ja": "貯蓄", "id": "Tabungan", "ms": "Tabungan"},
    "Documents": {"zh": "文件", "ko": "문서", "ja": "書類", "id": "Dokumen", "ms": "Dokumen"},
    "Invoices": {"zh": "发票", "ko": "송장", "ja": "請求書", "id": "Faktur", "ms": "Faktur"},
    "Invoices & Tax": {"zh": "发票与税务", "ko": "송장 및 세금", "ja": "請求書と税金", "id": "Faktur & Pajak", "ms": "Faktur & Pajak"},
    "Invoices and Tax": {"zh": "发票与税务", "ko": "송장 및 세금", "ja": "請求書と税金", "id": "Faktur dan Pajak", "ms": "Faktur dan Pajak"},
    "Tax": {"zh": "税务", "ko": "세금", "ja": "税金", "id": "Pajak", "ms": "Pajak"},
    "Privacy": {"zh": "隐私", "ko": "개인정보", "ja": "プライバシー", "id": "Privasi", "ms": "Privasi"},
    "Cloud": {"zh": "云端", "ko": "클라우드", "ja": "クラウド", "id": "Cloud", "ms": "Cloud"},

    # ── Common buttons / actions ────────────────────────────────────────
    "Save": {"zh": "保存", "ko": "저장", "ja": "保存", "id": "Simpan", "ms": "Simpan"},
    "Save Changes": {"zh": "保存更改", "ko": "변경사항 저장", "ja": "変更を保存", "id": "Simpan Perubahan", "ms": "Simpan Perubahan"},
    "Save Edit": {"zh": "保存编辑", "ko": "편집 저장", "ja": "編集を保存", "id": "Simpan Edit", "ms": "Simpan Edit"},
    "Save Edits": {"zh": "保存编辑", "ko": "편집 저장", "ja": "編集を保存", "id": "Simpan Perubahan", "ms": "Simpan Perubahan"},
    "Save Goal": {"zh": "保存目标", "ko": "목표 저장", "ja": "目標を保存", "id": "Simpan Target", "ms": "Simpan Target"},
    "Save Invoice": {"zh": "保存发票", "ko": "송장 저장", "ja": "請求書を保存", "id": "Simpan Faktur", "ms": "Simpan Faktur"},
    "Save My Data": {"zh": "保存我的数据", "ko": "내 데이터 저장", "ja": "データを保存", "id": "Simpan Data Saya", "ms": "Simpan Data Saya"},
    "Save Name": {"zh": "保存名称", "ko": "이름 저장", "ja": "名前を保存", "id": "Simpan Nama", "ms": "Simpan Nama"},
    "Save Status": {"zh": "保存状态", "ko": "상태 저장", "ja": "ステータスを保存", "id": "Simpan Status", "ms": "Simpan Status"},
    "Save Tax Settings": {"zh": "保存税务设置", "ko": "세금 설정 저장", "ja": "税金設定を保存", "id": "Simpan Pengaturan Pajak", "ms": "Simpan Pengaturan Pajak"},
    "Save Transaction": {"zh": "保存交易", "ko": "거래 저장", "ja": "取引を保存", "id": "Simpan Transaksi", "ms": "Simpan Transaksi"},
    "Saved.": {"zh": "已保存。", "ko": "저장됨.", "ja": "保存しました。", "id": "Tersimpan.", "ms": "Tersimpan."},
    "Cancel": {"zh": "取消", "ko": "취소", "ja": "キャンセル", "id": "Batal", "ms": "Batal"},
    "Delete": {"zh": "删除", "ko": "삭제", "ja": "削除", "id": "Hapus", "ms": "Hapus"},
    "Edit": {"zh": "编辑", "ko": "편집", "ja": "編集", "id": "Edit", "ms": "Edit"},
    "Add": {"zh": "添加", "ko": "추가", "ja": "追加", "id": "Tambah", "ms": "Tambah"},
    "Close": {"zh": "关闭", "ko": "닫기", "ja": "閉じる", "id": "Tutup", "ms": "Tutup"},
    "Confirm": {"zh": "确认", "ko": "확인", "ja": "確認", "id": "Konfirmasi", "ms": "Konfirmasi"},
    "Confirm Delete": {"zh": "确认删除", "ko": "삭제 확인", "ja": "削除を確認", "id": "Konfirmasi Hapus", "ms": "Konfirmasi Hapus"},
    "Confirm Deletion": {"zh": "确认删除", "ko": "삭제 확인", "ja": "削除を確認", "id": "Konfirmasi Penghapusan", "ms": "Konfirmasi Penghapusan"},
    "Confirm Document Deletion": {"zh": "确认删除文件", "ko": "문서 삭제 확인", "ja": "書類の削除を確認", "id": "Konfirmasi Hapus Dokumen", "ms": "Konfirmasi Hapus Dokumen"},
    "Confirm Delete Device Data": {"zh": "确认删除设备数据", "ko": "기기 데이터 삭제 확인", "ja": "デバイスデータの削除を確認", "id": "Konfirmasi Hapus Data Perangkat", "ms": "Konfirmasi Hapus Data Perangkat"},
    "Confirm project deletion": {"zh": "确认删除项目", "ko": "프로젝트 삭제 확인", "ja": "プロジェクトの削除を確認", "id": "Konfirmasi hapus proyek", "ms": "Konfirmasi hapus proyek"},
    "Done": {"zh": "完成", "ko": "완료", "ja": "完了", "id": "Selesai", "ms": "Selesai"},
    "Continue": {"zh": "继续", "ko": "계속", "ja": "続ける", "id": "Lanjutkan", "ms": "Lanjutkan"},
    "Yes": {"zh": "是", "ko": "예", "ja": "はい", "id": "Ya", "ms": "Ya"},
    "No": {"zh": "否", "ko": "아니오", "ja": "いいえ", "id": "Tidak", "ms": "Tidak"},
    "Search": {"zh": "搜索", "ko": "검색", "ja": "検索", "id": "Cari", "ms": "Cari"},
    "Export": {"zh": "导出", "ko": "내보내기", "ja": "エクスポート", "id": "Ekspor", "ms": "Ekspor"},
    "Export My Data": {"zh": "导出我的数据", "ko": "내 데이터 내보내기", "ja": "データをエクスポート", "id": "Ekspor Data Saya", "ms": "Ekspor Data Saya"},

    # ── Dashboard ───────────────────────────────────────────────────────
    "Flow · Control · Growth": {"zh": "Flow · Control · Growth", "ko": "Flow · Control · Growth", "ja": "Flow · Control · Growth", "id": "Flow · Control · Growth", "ms": "Flow · Control · Growth"},
    "This Month Overview": {"zh": "本月概览", "ko": "이번 달 개요", "ja": "今月の概要", "id": "Ringkasan Bulan Ini", "ms": "Ringkasan Bulan Ini"},
    "Income This Month": {"zh": "本月收入", "ko": "이번 달 수입", "ja": "今月の収入", "id": "Pendapatan Bulan Ini", "ms": "Pendapatan Bulan Ini"},
    "Expenses This Month": {"zh": "本月支出", "ko": "이번 달 지출", "ja": "今月の支出", "id": "Pengeluaran Bulan Ini", "ms": "Pengeluaran Bulan Ini"},
    "This Month Balance": {"zh": "本月余额", "ko": "이번 달 잔액", "ja": "今月の残高", "id": "Saldo Bulan Ini", "ms": "Saldo Bulan Ini"},
    "This Month Deposits": {"zh": "本月存款", "ko": "이번 달 입금", "ja": "今月の入金", "id": "Deposit Bulan Ini", "ms": "Deposit Bulan Ini"},
    "This Month Withdrawals": {"zh": "本月提款", "ko": "이번 달 출금", "ja": "今月の出金", "id": "Penarikan Bulan Ini", "ms": "Penarikan Bulan Ini"},
    "This Month": {"zh": "本月", "ko": "이번 달", "ja": "今月", "id": "Bulan Ini", "ms": "Bulan Ini"},
    "Income": {"zh": "收入", "ko": "수입", "ja": "収入", "id": "Pendapatan", "ms": "Pendapatan"},
    "Expense": {"zh": "支出", "ko": "지출", "ja": "支出", "id": "Pengeluaran", "ms": "Pengeluaran"},
    "Expenses": {"zh": "支出", "ko": "지출", "ja": "支出", "id": "Pengeluaran", "ms": "Pengeluaran"},
    "Net": {"zh": "净额", "ko": "순액", "ja": "純額", "id": "Bersih", "ms": "Bersih"},
    "Total": {"zh": "总计", "ko": "합계", "ja": "合計", "id": "Total", "ms": "Total"},
    "Total Income": {"zh": "总收入", "ko": "총 수입", "ja": "総収入", "id": "Total Pendapatan", "ms": "Total Pendapatan"},
    "Total Expenses": {"zh": "总支出", "ko": "총 지출", "ja": "総支出", "id": "Total Pengeluaran", "ms": "Total Pengeluaran"},
    "Overview": {"zh": "概览", "ko": "개요", "ja": "概要", "id": "Ringkasan", "ms": "Ringkasan"},
    "Selected Month": {"zh": "选定月份", "ko": "선택된 월", "ja": "選択月", "id": "Bulan Terpilih", "ms": "Bulan Terpilih"},
    "Newest First": {"zh": "最新优先", "ko": "최신순", "ja": "新しい順", "id": "Terbaru", "ms": "Terbaru"},
    "Oldest First": {"zh": "最早优先", "ko": "오래된순", "ja": "古い順", "id": "Terlama", "ms": "Terlama"},
    "Financial Analyzer": {"zh": "财务分析器", "ko": "재무 분석기", "ja": "財務アナライザー", "id": "Analisis Keuangan", "ms": "Analisis Keuangan"},
    "Open Financial Analyzer": {"zh": "打开财务分析器", "ko": "재무 분석기 열기", "ja": "財務アナライザーを開く", "id": "Buka Analisis Keuangan", "ms": "Buka Analisis Keuangan"},
    "Smart Summary": {"zh": "智能摘要", "ko": "스마트 요약", "ja": "スマート要約", "id": "Ringkasan Cerdas", "ms": "Ringkasan Cerdas"},

    # ── Account ─────────────────────────────────────────────────────────
    "Account Card": {"zh": "账户卡", "ko": "계좌 카드", "ja": "アカウントカード", "id": "Kartu Akun", "ms": "Kartu Akun"},
    "My Account": {"zh": "我的账户", "ko": "내 계좌", "ja": "マイアカウント", "id": "Akun Saya", "ms": "Akun Saya"},
    "Current Balance": {"zh": "当前余额", "ko": "현재 잔액", "ja": "現在の残高", "id": "Saldo Saat Ini", "ms": "Saldo Saat Ini"},
    "Transaction": {"zh": "交易", "ko": "거래", "ja": "取引", "id": "Transaksi", "ms": "Transaksi"},
    "Transactions": {"zh": "交易记录", "ko": "거래 내역", "ja": "取引一覧", "id": "Transaksi", "ms": "Transaksi"},
    "Transactions Count": {"zh": "交易数量", "ko": "거래 수", "ja": "取引数", "id": "Jumlah Transaksi", "ms": "Jumlah Transaksi"},
    "Add New Transaction": {"zh": "添加新交易", "ko": "새 거래 추가", "ja": "新規取引を追加", "id": "Tambah Transaksi Baru", "ms": "Tambah Transaksi Baru"},
    "Transaction added.": {"zh": "交易已添加。", "ko": "거래가 추가되었습니다.", "ja": "取引を追加しました。", "id": "Transaksi ditambahkan.", "ms": "Transaksi ditambahkan."},
    "Transaction recorded in account.": {"zh": "交易已记录到账户。", "ko": "계좌에 거래가 기록되었습니다.", "ja": "アカウントに取引を記録しました。", "id": "Transaksi dicatat di akun.", "ms": "Transaksi dicatat di akun."},
    "Record Payment": {"zh": "记录付款", "ko": "결제 기록", "ja": "支払いを記録", "id": "Catat Pembayaran", "ms": "Catat Pembayaran"},
    "Record Receipt": {"zh": "记录收款", "ko": "수금 기록", "ja": "入金を記録", "id": "Catat Penerimaan", "ms": "Catat Penerimaan"},
    "Record this transaction in account": {"zh": "在账户中记录此交易", "ko": "계좌에 이 거래를 기록", "ja": "アカウントにこの取引を記録", "id": "Catat transaksi ini di akun", "ms": "Catat transaksi ini di akun"},
    "Deposit": {"zh": "存款", "ko": "입금", "ja": "入金", "id": "Deposit", "ms": "Deposit"},
    "Withdraw": {"zh": "提款", "ko": "출금", "ja": "出金", "id": "Penarikan", "ms": "Penarikan"},
    "Income From Account": {"zh": "来自账户的收入", "ko": "계좌 수입", "ja": "アカウントからの収入", "id": "Pendapatan dari Akun", "ms": "Pendapatan dari Akun"},
    "Expense From Account": {"zh": "来自账户的支出", "ko": "계좌 지출", "ja": "アカウントからの支出", "id": "Pengeluaran dari Akun", "ms": "Pengeluaran dari Akun"},
    "From Account": {"zh": "来自账户", "ko": "계좌에서", "ja": "アカウントから", "id": "Dari Akun", "ms": "Dari Akun"},
    "No transactions for this month.": {"zh": "本月没有交易。", "ko": "이번 달 거래가 없습니다.", "ja": "今月の取引はありません。", "id": "Tidak ada transaksi bulan ini.", "ms": "Tidak ada transaksi bulan ini."},
    "Delete Selected": {"zh": "删除所选", "ko": "선택 삭제", "ja": "選択を削除", "id": "Hapus Terpilih", "ms": "Hapus Terpilih"},
    "Select at least one transaction.": {"zh": "请至少选择一笔交易。", "ko": "최소 하나의 거래를 선택하세요.", "ja": "少なくとも1つの取引を選択してください。", "id": "Pilih minimal satu transaksi.", "ms": "Pilih minimal satu transaksi."},
    "Select transactions to delete": {"zh": "选择要删除的交易", "ko": "삭제할 거래 선택", "ja": "削除する取引を選択", "id": "Pilih transaksi untuk dihapus", "ms": "Pilih transaksi untuk dihapus"},
    "Delete Selected Savings Transactions": {"zh": "删除所选储蓄交易", "ko": "선택한 저축 거래 삭제", "ja": "選択した貯蓄取引を削除", "id": "Hapus Transaksi Tabungan Terpilih", "ms": "Hapus Transaksi Tabungan Terpilih"},

    # ── Monthly items ───────────────────────────────────────────────────
    "Monthly": {"zh": "月度", "ko": "월간", "ja": "月次", "id": "Bulanan", "ms": "Bulanan"},
    "Monthly Amount": {"zh": "月度金额", "ko": "월 금액", "ja": "月額", "id": "Jumlah Bulanan", "ms": "Jumlah Bulanan"},
    "Monthly Estimate": {"zh": "月度预估", "ko": "월간 추정", "ja": "月次見積", "id": "Perkiraan Bulanan", "ms": "Perkiraan Bulanan"},
    "Active Monthly Items": {"zh": "活跃月度项目", "ko": "활성 월간 항목", "ja": "アクティブな月次項目", "id": "Item Bulanan Aktif", "ms": "Item Bulanan Aktif"},
    "Manage Monthly Items": {"zh": "管理月度项目", "ko": "월간 항목 관리", "ja": "月次項目を管理", "id": "Kelola Item Bulanan", "ms": "Kelola Item Bulanan"},
    "Close Monthly Items": {"zh": "关闭月度项目", "ko": "월간 항목 닫기", "ja": "月次項目を閉じる", "id": "Tutup Item Bulanan", "ms": "Tutup Item Bulanan"},
    "Hide Monthly Items": {"zh": "隐藏月度项目", "ko": "월간 항목 숨기기", "ja": "月次項目を非表示", "id": "Sembunyikan Item Bulanan", "ms": "Sembunyikan Item Bulanan"},
    "Manage commitments and income (add, edit, delete)": {"zh": "管理承诺和收入（添加、编辑、删除）", "ko": "약정 및 수입 관리 (추가, 편집, 삭제)", "ja": "コミットメントと収入を管理（追加・編集・削除）", "id": "Kelola komitmen dan pendapatan (tambah, edit, hapus)", "ms": "Kelola komitmen dan pendapatan (tambah, edit, hapus)"},
    "Add or edit monthly commitments and income": {"zh": "添加或编辑月度承诺和收入", "ko": "월간 약정 및 수입 추가 또는 편집", "ja": "月次コミットメントと収入を追加・編集", "id": "Tambah atau edit komitmen dan pendapatan bulanan", "ms": "Tambah atau edit komitmen dan pendapatan bulanan"},
    "No monthly items yet. Start by adding your first item from Manage Monthly Items.": {"zh": "还没有月度项目。从「管理月度项目」开始添加。", "ko": "아직 월간 항목이 없습니다. 월간 항목 관리에서 첫 항목을 추가하세요.", "ja": "月次項目がまだありません。月次項目管理から最初の項目を追加してください。", "id": "Belum ada item bulanan. Mulai dengan menambahkan item pertama dari Kelola Item Bulanan.", "ms": "Belum ada item bulanan. Mulai dengan menambahkan item pertama dari Kelola Item Bulanan."},
    "Item Name": {"zh": "项目名称", "ko": "항목명", "ja": "項目名", "id": "Nama Item", "ms": "Nama Item"},
    "Item": {"zh": "项目", "ko": "항목", "ja": "項目", "id": "Item", "ms": "Item"},
    "Items": {"zh": "项目", "ko": "항목", "ja": "項目", "id": "Item", "ms": "Item"},
    "Item added successfully.": {"zh": "项目添加成功。", "ko": "항목이 추가되었습니다.", "ja": "項目を追加しました。", "id": "Item berhasil ditambahkan.", "ms": "Item berhasil ditambahkan."},
    "Item deleted.": {"zh": "项目已删除。", "ko": "항목이 삭제되었습니다.", "ja": "項目を削除しました。", "id": "Item dihapus.", "ms": "Item dihapus."},
    "Item updated.": {"zh": "项目已更新。", "ko": "항목이 업데이트되었습니다.", "ja": "項目を更新しました。", "id": "Item diperbarui.", "ms": "Item diperbarui."},
    "Add New Item": {"zh": "添加新项目", "ko": "새 항목 추가", "ja": "新規項目を追加", "id": "Tambah Item Baru", "ms": "Tambah Item Baru"},
    "Default Amount": {"zh": "默认金额", "ko": "기본 금액", "ja": "デフォルト金額", "id": "Jumlah Default", "ms": "Jumlah Default"},
    "Update default amount permanently": {"zh": "永久更新默认金额", "ko": "기본 금액 영구 업데이트", "ja": "デフォルト金額を恒久的に更新", "id": "Perbarui jumlah default secara permanen", "ms": "Perbarui jumlah default secara permanen"},

    # ── Entitlements ────────────────────────────────────────────────────
    "Entitlement Month": {"zh": "权益月", "ko": "수급 월", "ja": "帰属月", "id": "Bulan Hak", "ms": "Bulan Hak"},
    "Entitlements": {"zh": "权益", "ko": "수급", "ja": "帰属", "id": "Hak", "ms": "Hak"},
    "Entitlements and Coverage": {"zh": "权益与覆盖", "ko": "수급 및 커버리지", "ja": "帰属とカバレッジ", "id": "Hak dan Cakupan", "ms": "Hak dan Cakupan"},
    "Entitlement Coverage Net": {"zh": "权益覆盖净额", "ko": "수급 커버리지 순액", "ja": "帰属カバレッジ純額", "id": "Cakupan Hak Bersih", "ms": "Cakupan Hak Bersih"},
    "Current Entitlement Net": {"zh": "当前权益净额", "ko": "현재 수급 순액", "ja": "現在の帰属純額", "id": "Hak Bersih Saat Ini", "ms": "Hak Bersih Saat Ini"},
    "Unconfirmed Entitlement Net": {"zh": "未确认权益净额", "ko": "미확인 수급 순액", "ja": "未確認帰属純額", "id": "Hak Bersih Belum Dikonfirmasi", "ms": "Hak Bersih Belum Dikonfirmasi"},
    "No entitlement months waiting for confirmation.": {"zh": "没有等待确认的权益月。", "ko": "확인 대기중인 수급 월이 없습니다.", "ja": "確認待ちの帰属月はありません。", "id": "Tidak ada bulan hak yang menunggu konfirmasi.", "ms": "Tidak ada bulan hak yang menunggu konfirmasi."},
    "Last confirmed month": {"zh": "最后确认月", "ko": "마지막 확인 월", "ja": "最後の確認月", "id": "Bulan terakhir dikonfirmasi", "ms": "Bulan terakhir dikonfirmasi"},
    "Last confirmed month (if any)": {"zh": "最后确认月（如有）", "ko": "마지막 확인 월 (있는 경우)", "ja": "最後の確認月（ある場合）", "id": "Bulan terakhir dikonfirmasi (jika ada)", "ms": "Bulan terakhir dikonfirmasi (jika ada)"},
    "Recorded Month": {"zh": "记录月份", "ko": "기록 월", "ja": "記録月", "id": "Bulan Tercatat", "ms": "Bulan Tercatat"},

    # ── Expected / Projected ────────────────────────────────────────────
    "Expected Income": {"zh": "预期收入", "ko": "예상 수입", "ja": "予想収入", "id": "Pendapatan yang Diharapkan", "ms": "Pendapatan yang Diharapkan"},
    "Expected Expenses": {"zh": "预期支出", "ko": "예상 지출", "ja": "予想支出", "id": "Pengeluaran yang Diharapkan", "ms": "Pengeluaran yang Diharapkan"},
    "Expected Net": {"zh": "预期净额", "ko": "예상 순액", "ja": "予想純額", "id": "Bersih yang Diharapkan", "ms": "Bersih yang Diharapkan"},
    "Expected Net After Settle": {"zh": "结算后预期净额", "ko": "정산 후 예상 순액", "ja": "決済後予想純額", "id": "Bersih yang Diharapkan Setelah Selesai", "ms": "Bersih yang Diharapkan Setelah Selesai"},
    "Expected Income Not Received": {"zh": "未收到的预期收入", "ko": "미수 예상 수입", "ja": "未受領予想収入", "id": "Pendapatan yang Diharapkan Belum Diterima", "ms": "Pendapatan yang Diharapkan Belum Diterima"},
    "Expected Receipt Day": {"zh": "预期收款日", "ko": "예상 수금일", "ja": "予想入金日", "id": "Hari Penerimaan yang Diharapkan", "ms": "Hari Penerimaan yang Diharapkan"},
    "Expected receipt day": {"zh": "预期收款日", "ko": "예상 수금일", "ja": "予想入金日", "id": "Hari penerimaan yang diharapkan", "ms": "Hari penerimaan yang diharapkan"},
    "Projected Income": {"zh": "预测收入", "ko": "예측 수입", "ja": "予測収入", "id": "Proyeksi Pendapatan", "ms": "Proyeksi Pendapatan"},
    "Projected Expense": {"zh": "预测支出", "ko": "예측 지출", "ja": "予測支出", "id": "Proyeksi Pengeluaran", "ms": "Proyeksi Pengeluaran"},
    "Projected Net": {"zh": "预测净额", "ko": "예측 순액", "ja": "予測純額", "id": "Proyeksi Bersih", "ms": "Proyeksi Bersih"},
    "Projected Net Next 90 Days": {"zh": "未来90天预测净额", "ko": "향후 90일 예측 순액", "ja": "今後90日間の予測純額", "id": "Proyeksi Bersih 90 Hari Ke Depan", "ms": "Proyeksi Bersih 90 Hari Ke Depan"},
    "Total Expected Income Not Received": {"zh": "未收到的预期收入总额", "ko": "미수 예상 수입 총액", "ja": "未受領予想収入合計", "id": "Total Pendapatan yang Diharapkan Belum Diterima", "ms": "Total Pendapatan yang Diharapkan Belum Diterima"},

    # ── 90-Day analysis ─────────────────────────────────────────────────
    "90-Day Cash Flow": {"zh": "90天现金流", "ko": "90일 현금흐름", "ja": "90日キャッシュフロー", "id": "Arus Kas 90 Hari", "ms": "Arus Kas 90 Hari"},
    "90-Day Outlook": {"zh": "90天展望", "ko": "90일 전망", "ja": "90日見通し", "id": "Prospek 90 Hari", "ms": "Prospek 90 Hari"},
    "Net Last 90 Days": {"zh": "过去90天净额", "ko": "최근 90일 순액", "ja": "過去90日間純額", "id": "Bersih 90 Hari Terakhir", "ms": "Bersih 90 Hari Terakhir"},
    "Delta vs Last 90 Days": {"zh": "与过去90天的差异", "ko": "최근 90일 대비 변화", "ja": "過去90日間との差異", "id": "Perubahan vs 90 Hari Terakhir", "ms": "Perubahan vs 90 Hari Terakhir"},
    "6-Month Average": {"zh": "6个月平均", "ko": "6개월 평균", "ja": "6ヶ月平均", "id": "Rata-rata 6 Bulan", "ms": "Rata-rata 6 Bulan"},
    "Peak Expense Month": {"zh": "支出最高月", "ko": "최고 지출 월", "ja": "支出最高月", "id": "Bulan Pengeluaran Tertinggi", "ms": "Bulan Pengeluaran Tertinggi"},
    "Your spending is above the 6-month average.": {"zh": "您的支出高于6个月平均水平。", "ko": "지출이 6개월 평균보다 높습니다.", "ja": "支出が6ヶ月平均を上回っています。", "id": "Pengeluaran Anda di atas rata-rata 6 bulan.", "ms": "Pengeluaran Anda di atas rata-rata 6 bulan."},
    "Your spending is below the 6-month average.": {"zh": "您的支出低于6个月平均水平。", "ko": "지출이 6개월 평균보다 낮습니다.", "ja": "支出が6ヶ月平均を下回っています。", "id": "Pengeluaran Anda di bawah rata-rata 6 bulan.", "ms": "Pengeluaran Anda di bawah rata-rata 6 bulan."},
    "Your spending is close to your usual average.": {"zh": "您的支出接近平均水平。", "ko": "지출이 평균 수준에 가깝습니다.", "ja": "支出は平均に近い水準です。", "id": "Pengeluaran Anda mendekati rata-rata biasa.", "ms": "Pengeluaran Anda mendekati rata-rata biasa."},
    "Seasonal Expense Behavior": {"zh": "季节性支出行为", "ko": "계절별 지출 패턴", "ja": "季節性支出パターン", "id": "Perilaku Pengeluaran Musiman", "ms": "Perilaku Pengeluaran Musiman"},

    # ── Overdue / Status ────────────────────────────────────────────────
    "Overdue": {"zh": "逾期", "ko": "연체", "ja": "延滞", "id": "Terlambat", "ms": "Terlambat"},
    "Due": {"zh": "到期", "ko": "만기", "ja": "期日", "id": "Jatuh Tempo", "ms": "Jatuh Tempo"},
    "Due Date": {"zh": "到期日", "ko": "만기일", "ja": "期日", "id": "Tanggal Jatuh Tempo", "ms": "Tanggal Jatuh Tempo"},
    "Due day": {"zh": "到期日", "ko": "만기일", "ja": "期日", "id": "Tanggal jatuh tempo", "ms": "Tanggal jatuh tempo"},
    "Due Payment Day": {"zh": "付款到期日", "ko": "결제 만기일", "ja": "支払期日", "id": "Hari Pembayaran Jatuh Tempo", "ms": "Hari Pembayaran Jatuh Tempo"},
    "Set Due Date": {"zh": "设置到期日", "ko": "만기일 설정", "ja": "期日を設定", "id": "Atur Tanggal Jatuh Tempo", "ms": "Atur Tanggal Jatuh Tempo"},
    "Has Due Date": {"zh": "有到期日", "ko": "만기일 있음", "ja": "期日あり", "id": "Ada Tanggal Jatuh Tempo", "ms": "Ada Tanggal Jatuh Tempo"},
    "Overdue Commitments (Unpaid)": {"zh": "逾期承诺（未付）", "ko": "연체 약정 (미지급)", "ja": "延滞コミットメント（未払い）", "id": "Komitmen Terlambat (Belum Dibayar)", "ms": "Komitmen Terlambat (Belum Dibayar)"},
    "Overdue Document Fees": {"zh": "逾期文件费用", "ko": "연체 문서 수수료", "ja": "延滞書類手数料", "id": "Biaya Dokumen Terlambat", "ms": "Biaya Dokumen Terlambat"},
    "Overdue Open Invoices": {"zh": "逾期未结发票", "ko": "연체 미결 송장", "ja": "延滞未決済請求書", "id": "Faktur Terbuka Terlambat", "ms": "Faktur Terbuka Terlambat"},
    "Total Overdue Commitments": {"zh": "逾期承诺总额", "ko": "연체 약정 총액", "ja": "延滞コミットメント合計", "id": "Total Komitmen Terlambat", "ms": "Total Komitmen Terlambat"},
    "Total Expenses Awaiting Payment": {"zh": "待付支出总额", "ko": "미지급 지출 총액", "ja": "未払い支出合計", "id": "Total Pengeluaran Menunggu Pembayaran", "ms": "Total Pengeluaran Menunggu Pembayaran"},
    "Active": {"zh": "活跃", "ko": "활성", "ja": "アクティブ", "id": "Aktif", "ms": "Aktif"},
    "Paused": {"zh": "暂停", "ko": "일시중지", "ja": "一時停止", "id": "Dijeda", "ms": "Dijeda"},
    "Cancelled": {"zh": "已取消", "ko": "취소됨", "ja": "キャンセル済み", "id": "Dibatalkan", "ms": "Dibatalkan"},
    "Paid": {"zh": "已付", "ko": "지급완료", "ja": "支払済", "id": "Dibayar", "ms": "Dibayar"},
    "Received": {"zh": "已收", "ko": "수금완료", "ja": "受領済", "id": "Diterima", "ms": "Diterima"},
    "Paid Date": {"zh": "付款日期", "ko": "지급일", "ja": "支払日", "id": "Tanggal Dibayar", "ms": "Tanggal Dibayar"},
    "Status": {"zh": "状态", "ko": "상태", "ja": "ステータス", "id": "Status", "ms": "Status"},
    "New Status": {"zh": "新状态", "ko": "새 상태", "ja": "新しいステータス", "id": "Status Baru", "ms": "Status Baru"},
    "Status updated.": {"zh": "状态已更新。", "ko": "상태가 업데이트되었습니다.", "ja": "ステータスを更新しました。", "id": "Status diperbarui.", "ms": "Status diperbarui."},
    "Filter Status": {"zh": "筛选状态", "ko": "상태 필터", "ja": "ステータスフィルター", "id": "Filter Status", "ms": "Filter Status"},

    # ── Fields / labels ─────────────────────────────────────────────────
    "Date": {"zh": "日期", "ko": "날짜", "ja": "日付", "id": "Tanggal", "ms": "Tanggal"},
    "Amount": {"zh": "金额", "ko": "금액", "ja": "金額", "id": "Jumlah", "ms": "Jumlah"},
    "Actual Amount": {"zh": "实际金额", "ko": "실제 금액", "ja": "実際の金額", "id": "Jumlah Aktual", "ms": "Jumlah Aktual"},
    "Variable Amount": {"zh": "可变金额", "ko": "변동 금액", "ja": "変動金額", "id": "Jumlah Variabel", "ms": "Jumlah Variabel"},
    "Currency": {"zh": "货币", "ko": "통화", "ja": "通貨", "id": "Mata Uang", "ms": "Mata Uang"},
    "Default Currency": {"zh": "默认货币", "ko": "기본 통화", "ja": "デフォルト通貨", "id": "Mata Uang Default", "ms": "Mata Uang Default"},
    "Use Default Currency": {"zh": "使用默认货币", "ko": "기본 통화 사용", "ja": "デフォルト通貨を使用", "id": "Gunakan Mata Uang Default", "ms": "Gunakan Mata Uang Default"},
    "Category": {"zh": "类别", "ko": "카테고리", "ja": "カテゴリ", "id": "Kategori", "ms": "Kategori"},
    "Type": {"zh": "类型", "ko": "유형", "ja": "タイプ", "id": "Tipe", "ms": "Tipe"},
    "Name cannot be empty.": {"zh": "名称不能为空。", "ko": "이름을 입력해주세요.", "ja": "名前を入力してください。", "id": "Nama tidak boleh kosong.", "ms": "Nama tidak boleh kosong."},
    "Note": {"zh": "备注", "ko": "메모", "ja": "メモ", "id": "Catatan", "ms": "Catatan"},
    "Note (Optional)": {"zh": "备注（可选）", "ko": "메모 (선택)", "ja": "メモ（任意）", "id": "Catatan (Opsional)", "ms": "Catatan (Opsional)"},
    "Notes": {"zh": "备注", "ko": "메모", "ja": "メモ", "id": "Catatan", "ms": "Catatan"},
    "Number": {"zh": "编号", "ko": "번호", "ja": "番号", "id": "Nomor", "ms": "Nomor"},
    "Order": {"zh": "订单", "ko": "주문", "ja": "注文", "id": "Pesanan", "ms": "Pesanan"},
    "Source": {"zh": "来源", "ko": "출처", "ja": "ソース", "id": "Sumber", "ms": "Sumber"},
    "Section": {"zh": "部分", "ko": "섹션", "ja": "セクション", "id": "Bagian", "ms": "Bagian"},
    "Period": {"zh": "期间", "ko": "기간", "ja": "期間", "id": "Periode", "ms": "Periode"},
    "Month": {"zh": "月", "ko": "월", "ja": "月", "id": "Bulan", "ms": "Bulan"},
    "Year": {"zh": "年", "ko": "연도", "ja": "年", "id": "Tahun", "ms": "Tahun"},
    "Action": {"zh": "操作", "ko": "작업", "ja": "アクション", "id": "Tindakan", "ms": "Tindakan"},
    "Rank": {"zh": "排名", "ko": "순위", "ja": "ランク", "id": "Peringkat", "ms": "Peringkat"},
    "Movement Date": {"zh": "交易日期", "ko": "이동 날짜", "ja": "移動日", "id": "Tanggal Pergerakan", "ms": "Tanggal Pergerakan"},
    "Actual Payment/Receipt Date": {"zh": "实际付款/收款日期", "ko": "실제 결제/수금일", "ja": "実際の支払い/入金日", "id": "Tanggal Pembayaran/Penerimaan Aktual", "ms": "Tanggal Pembayaran/Penerimaan Aktual"},
    "Hello": {"zh": "你好", "ko": "안녕하세요", "ja": "こんにちは", "id": "Halo", "ms": "Halo"},

    # ── Savings ─────────────────────────────────────────────────────────
    "Savings Card": {"zh": "储蓄卡", "ko": "저축 카드", "ja": "貯蓄カード", "id": "Kartu Tabungan", "ms": "Kartu Tabungan"},
    "Savings Balance": {"zh": "储蓄余额", "ko": "저축 잔액", "ja": "貯蓄残高", "id": "Saldo Tabungan", "ms": "Saldo Tabungan"},
    "Savings Net (All Months)": {"zh": "储蓄净额（所有月份）", "ko": "저축 순액 (전체 월)", "ja": "貯蓄純額（全月）", "id": "Tabungan Bersih (Semua Bulan)", "ms": "Tabungan Bersih (Semua Bulan)"},
    "Total Savings (All Months)": {"zh": "总储蓄（所有月份）", "ko": "총 저축 (전체 월)", "ja": "総貯蓄（全月）", "id": "Total Tabungan (Semua Bulan)", "ms": "Total Tabungan (Semua Bulan)"},
    "Total Savings Goal": {"zh": "总储蓄目标", "ko": "총 저축 목표", "ja": "総貯蓄目標", "id": "Target Tabungan Total", "ms": "Target Tabungan Total"},
    "Savings and Projects": {"zh": "储蓄与项目", "ko": "저축 및 프로젝트", "ja": "貯蓄とプロジェクト", "id": "Tabungan dan Proyek", "ms": "Tabungan dan Proyek"},
    "Add Savings Transaction": {"zh": "添加储蓄交易", "ko": "저축 거래 추가", "ja": "貯蓄取引を追加", "id": "Tambah Transaksi Tabungan", "ms": "Tambah Transaksi Tabungan"},
    "Savings transaction saved.": {"zh": "储蓄交易已保存。", "ko": "저축 거래가 저장되었습니다.", "ja": "貯蓄取引を保存しました。", "id": "Transaksi tabungan tersimpan.", "ms": "Transaksi tabungan tersimpan."},
    "No saved items yet.": {"zh": "还没有储蓄项目。", "ko": "아직 저축 항목이 없습니다.", "ja": "まだ貯蓄項目がありません。", "id": "Belum ada item tersimpan.", "ms": "Belum ada item tersimpan."},

    # ── Purchase goals ──────────────────────────────────────────────────
    "Active Goals": {"zh": "活跃目标", "ko": "활성 목표", "ja": "アクティブな目標", "id": "Target Aktif", "ms": "Target Aktif"},
    "Add Purchase Goal": {"zh": "添加购买目标", "ko": "구매 목표 추가", "ja": "購入目標を追加", "id": "Tambah Target Pembelian", "ms": "Tambah Target Pembelian"},
    "Goal Name": {"zh": "目标名称", "ko": "목표명", "ja": "目標名", "id": "Nama Target", "ms": "Nama Target"},
    "Goal saved.": {"zh": "目标已保存。", "ko": "목표가 저장되었습니다.", "ja": "目標を保存しました。", "id": "Target tersimpan.", "ms": "Target tersimpan."},
    "Goal updated.": {"zh": "目标已更新。", "ko": "목표가 업데이트되었습니다.", "ja": "目標を更新しました。", "id": "Target diperbarui.", "ms": "Target diperbarui."},
    "Goal deleted.": {"zh": "目标已删除。", "ko": "목표가 삭제되었습니다.", "ja": "目標を削除しました。", "id": "Target dihapus.", "ms": "Target dihapus."},
    "Delete Goal": {"zh": "删除目标", "ko": "목표 삭제", "ja": "目標を削除", "id": "Hapus Target", "ms": "Hapus Target"},
    "No purchase goals yet.": {"zh": "还没有购买目标。", "ko": "아직 구매 목표가 없습니다.", "ja": "購入目標はまだありません。", "id": "Belum ada target pembelian.", "ms": "Belum ada target pembelian."},
    "Target Amount": {"zh": "目标金额", "ko": "목표 금액", "ja": "目標金額", "id": "Jumlah Target", "ms": "Jumlah Target"},
    "Target Date": {"zh": "目标日期", "ko": "목표일", "ja": "目標日", "id": "Tanggal Target", "ms": "Tanggal Target"},
    "Target": {"zh": "目标", "ko": "목표", "ja": "目標", "id": "Target", "ms": "Target"},
    "Target amount must be greater than zero.": {"zh": "目标金额必须大于零。", "ko": "목표 금액은 0보다 커야 합니다.", "ja": "目標金額は0より大きくなければなりません。", "id": "Jumlah target harus lebih dari nol.", "ms": "Jumlah target harus lebih dari nol."},
    "Currently Saved": {"zh": "已储蓄", "ko": "현재 저축", "ja": "現在の貯蓄", "id": "Saat Ini Tersimpan", "ms": "Saat Ini Tersimpan"},
    "Remaining": {"zh": "剩余", "ko": "남은", "ja": "残り", "id": "Sisa", "ms": "Sisa"},
    "Total Remaining": {"zh": "剩余总额", "ko": "남은 총액", "ja": "残り合計", "id": "Total Sisa", "ms": "Total Sisa"},
    "Suggested Monthly Amount": {"zh": "建议月度金额", "ko": "추천 월 금액", "ja": "推奨月額", "id": "Jumlah Bulanan yang Disarankan", "ms": "Jumlah Bulanan yang Disarankan"},
    "Allocated": {"zh": "已分配", "ko": "할당됨", "ja": "割当済", "id": "Dialokasikan", "ms": "Dialokasikan"},
    "Please enter a goal name first.": {"zh": "请先输入目标名称。", "ko": "먼저 목표명을 입력하세요.", "ja": "まず目標名を入力してください。", "id": "Silakan masukkan nama target terlebih dahulu.", "ms": "Silakan masukkan nama target terlebih dahulu."},
    "Please enter a valid name and amount.": {"zh": "请输入有效的名称和金额。", "ko": "유효한 이름과 금액을 입력하세요.", "ja": "有効な名前と金額を入力してください。", "id": "Silakan masukkan nama dan jumlah yang valid.", "ms": "Silakan masukkan nama dan jumlah yang valid."},
    "Unnamed Goal": {"zh": "未命名目标", "ko": "이름 없는 목표", "ja": "名称未設定の目標", "id": "Target Tanpa Nama", "ms": "Target Tanpa Nama"},

    # ── Projects ────────────────────────────────────────────────────────
    "Active Projects": {"zh": "活跃项目", "ko": "활성 프로젝트", "ja": "アクティブなプロジェクト", "id": "Proyek Aktif", "ms": "Proyek Aktif"},
    "Add Project": {"zh": "添加项目", "ko": "프로젝트 추가", "ja": "プロジェクトを追加", "id": "Tambah Proyek", "ms": "Tambah Proyek"},
    "＋ Add Project": {"zh": "＋ 添加项目", "ko": "＋ 프로젝트 추가", "ja": "＋ プロジェクトを追加", "id": "＋ Tambah Proyek", "ms": "＋ Tambah Proyek"},
    "Add Project Transaction": {"zh": "添加项目交易", "ko": "프로젝트 거래 추가", "ja": "プロジェクト取引を追加", "id": "Tambah Transaksi Proyek", "ms": "Tambah Transaksi Proyek"},
    "Project": {"zh": "项目", "ko": "프로젝트", "ja": "プロジェクト", "id": "Proyek", "ms": "Proyek"},
    "Project Name": {"zh": "项目名称", "ko": "프로젝트명", "ja": "プロジェクト名", "id": "Nama Proyek", "ms": "Nama Proyek"},
    "Project Type": {"zh": "项目类型", "ko": "프로젝트 유형", "ja": "プロジェクトタイプ", "id": "Tipe Proyek", "ms": "Tipe Proyek"},
    "Project Details": {"zh": "项目详情", "ko": "프로젝트 상세", "ja": "プロジェクト詳細", "id": "Detail Proyek", "ms": "Detail Proyek"},
    "Project Notes": {"zh": "项目备注", "ko": "프로젝트 메모", "ja": "プロジェクトメモ", "id": "Catatan Proyek", "ms": "Catatan Proyek"},
    "Project Summary": {"zh": "项目摘要", "ko": "프로젝트 요약", "ja": "プロジェクト概要", "id": "Ringkasan Proyek", "ms": "Ringkasan Proyek"},
    "Manage Project": {"zh": "管理项目", "ko": "프로젝트 관리", "ja": "プロジェクトを管理", "id": "Kelola Proyek", "ms": "Kelola Proyek"},
    "Delete Project": {"zh": "删除项目", "ko": "프로젝트 삭제", "ja": "プロジェクトを削除", "id": "Hapus Proyek", "ms": "Hapus Proyek"},
    "Rename Project": {"zh": "重命名项目", "ko": "프로젝트 이름 변경", "ja": "プロジェクト名を変更", "id": "Ubah Nama Proyek", "ms": "Ubah Nama Proyek"},
    "Project added.": {"zh": "项目已添加。", "ko": "프로젝트가 추가되었습니다.", "ja": "プロジェクトを追加しました。", "id": "Proyek ditambahkan.", "ms": "Proyek ditambahkan."},
    "Project deleted.": {"zh": "项目已删除。", "ko": "프로젝트가 삭제되었습니다.", "ja": "プロジェクトを削除しました。", "id": "Proyek dihapus.", "ms": "Proyek dihapus."},
    "Project name already exists.": {"zh": "项目名称已存在。", "ko": "프로젝트명이 이미 존재합니다.", "ja": "プロジェクト名は既に存在します。", "id": "Nama proyek sudah ada.", "ms": "Nama proyek sudah ada."},
    "Project name updated.": {"zh": "项目名称已更新。", "ko": "프로젝트명이 업데이트되었습니다.", "ja": "プロジェクト名を更新しました。", "id": "Nama proyek diperbarui.", "ms": "Nama proyek diperbarui."},
    "Project transaction saved.": {"zh": "项目交易已保存。", "ko": "프로젝트 거래가 저장되었습니다.", "ja": "プロジェクト取引を保存しました。", "id": "Transaksi proyek tersimpan.", "ms": "Transaksi proyek tersimpan."},
    "No projects yet. Use Add Project to create one.": {"zh": "还没有项目。使用「添加项目」创建。", "ko": "아직 프로젝트가 없습니다. 프로젝트 추가로 생성하세요.", "ja": "プロジェクトがまだありません。「プロジェクトを追加」で作成してください。", "id": "Belum ada proyek. Gunakan Tambah Proyek untuk membuat.", "ms": "Belum ada proyek. Gunakan Tambah Proyek untuk membuat."},
    "No project-linked data this month.": {"zh": "本月没有项目相关数据。", "ko": "이번 달 프로젝트 관련 데이터가 없습니다.", "ja": "今月のプロジェクトデータはありません。", "id": "Tidak ada data terkait proyek bulan ini.", "ms": "Tidak ada data terkait proyek bulan ini."},
    "No transactions for this project this month.": {"zh": "本月该项目没有交易。", "ko": "이번 달 이 프로젝트의 거래가 없습니다.", "ja": "今月このプロジェクトの取引はありません。", "id": "Tidak ada transaksi untuk proyek ini bulan ini.", "ms": "Tidak ada transaksi untuk proyek ini bulan ini."},
    "No Project": {"zh": "无项目", "ko": "프로젝트 없음", "ja": "プロジェクトなし", "id": "Tanpa Proyek", "ms": "Tanpa Proyek"},
    "Please enter the project name first.": {"zh": "请先输入项目名称。", "ko": "먼저 프로젝트명을 입력하세요.", "ja": "まずプロジェクト名を入力してください。", "id": "Silakan masukkan nama proyek terlebih dahulu.", "ms": "Silakan masukkan nama proyek terlebih dahulu."},
    "Projects Card": {"zh": "项目卡", "ko": "프로젝트 카드", "ja": "プロジェクトカード", "id": "Kartu Proyek", "ms": "Kartu Proyek"},
    "Projects Comparison": {"zh": "项目比较", "ko": "프로젝트 비교", "ja": "プロジェクト比較", "id": "Perbandingan Proyek", "ms": "Perbandingan Proyek"},
    "Projects Net (All Months)": {"zh": "项目净额（所有月份）", "ko": "프로젝트 순액 (전체 월)", "ja": "プロジェクト純額（全月）", "id": "Proyek Bersih (Semua Bulan)", "ms": "Proyek Bersih (Semua Bulan)"},
    "Projects Net This Month": {"zh": "本月项目净额", "ko": "이번 달 프로젝트 순액", "ja": "今月のプロジェクト純額", "id": "Proyek Bersih Bulan Ini", "ms": "Proyek Bersih Bulan Ini"},
    "All Projects Net": {"zh": "所有项目净额", "ko": "전체 프로젝트 순액", "ja": "全プロジェクト純額", "id": "Semua Proyek Bersih", "ms": "Semua Proyek Bersih"},
    "Selected Project Net": {"zh": "选定项目净额", "ko": "선택 프로젝트 순액", "ja": "選択プロジェクト純額", "id": "Proyek Terpilih Bersih", "ms": "Proyek Terpilih Bersih"},
    "Strongest Project": {"zh": "最强项目", "ko": "최고 프로젝트", "ja": "最優秀プロジェクト", "id": "Proyek Terkuat", "ms": "Proyek Terkuat"},
    "Weakest Project": {"zh": "最弱项目", "ko": "최약 프로젝트", "ja": "最弱プロジェクト", "id": "Proyek Terlemah", "ms": "Proyek Terlemah"},
    "Linked Project": {"zh": "关联项目", "ko": "연결된 프로젝트", "ja": "リンクされたプロジェクト", "id": "Proyek Terkait", "ms": "Proyek Terkait"},
    "Unlinked": {"zh": "未关联", "ko": "미연결", "ja": "未リンク", "id": "Tidak Terkait", "ms": "Tidak Terkait"},
    "From Project": {"zh": "来自项目", "ko": "프로젝트에서", "ja": "プロジェクトから", "id": "Dari Proyek", "ms": "Dari Proyek"},
    "Transfer to project": {"zh": "转移到项目", "ko": "프로젝트로 이체", "ja": "プロジェクトに転送", "id": "Transfer ke proyek", "ms": "Transfer ke proyek"},
    "Project Transfer": {"zh": "项目转移", "ko": "프로젝트 이체", "ja": "プロジェクト転送", "id": "Transfer Proyek", "ms": "Transfer Proyek"},
    "Project expense": {"zh": "项目支出", "ko": "프로젝트 지출", "ja": "プロジェクト支出", "id": "Pengeluaran proyek", "ms": "Pengeluaran proyek"},
    "Estimated Project Support": {"zh": "预估项目支持", "ko": "예상 프로젝트 지원", "ja": "推定プロジェクトサポート", "id": "Estimasi Dukungan Proyek", "ms": "Estimasi Dukungan Proyek"},
    "Personal Net Before Support": {"zh": "支持前个人净额", "ko": "지원 전 개인 순액", "ja": "サポート前個人純額", "id": "Bersih Pribadi Sebelum Dukungan", "ms": "Bersih Pribadi Sebelum Dukungan"},
    "Personal Net After Support": {"zh": "支持后个人净额", "ko": "지원 후 개인 순액", "ja": "サポート後個人純額", "id": "Bersih Pribadi Setelah Dukungan", "ms": "Bersih Pribadi Setelah Dukungan"},
    "Actual Net Now": {"zh": "当前实际净额", "ko": "현재 실제 순액", "ja": "現在の実際純額", "id": "Bersih Aktual Saat Ini", "ms": "Bersih Aktual Saat Ini"},

    # ── Documents ───────────────────────────────────────────────────────
    "Documents Count": {"zh": "文件数量", "ko": "문서 수", "ja": "書類数", "id": "Jumlah Dokumen", "ms": "Jumlah Dokumen"},
    "Add Document": {"zh": "添加文件", "ko": "문서 추가", "ja": "書類を追加", "id": "Tambah Dokumen", "ms": "Tambah Dokumen"},
    "Add document": {"zh": "添加文件", "ko": "문서 추가", "ja": "書類を追加", "id": "Tambah dokumen", "ms": "Tambah dokumen"},
    "Document": {"zh": "文件", "ko": "문서", "ja": "書類", "id": "Dokumen", "ms": "Dokumen"},
    "Document Name": {"zh": "文件名称", "ko": "문서명", "ja": "書類名", "id": "Nama Dokumen", "ms": "Nama Dokumen"},
    "Document deleted.": {"zh": "文件已删除。", "ko": "문서가 삭제되었습니다.", "ja": "書類を削除しました。", "id": "Dokumen dihapus.", "ms": "Dokumen dihapus."},
    "Delete Document": {"zh": "删除文件", "ko": "문서 삭제", "ja": "書類を削除", "id": "Hapus Dokumen", "ms": "Hapus Dokumen"},
    "Document management and renewal reminders": {"zh": "文件管理与续期提醒", "ko": "문서 관리 및 갱신 알림", "ja": "書類管理と更新リマインダー", "id": "Manajemen dokumen dan pengingat perpanjangan", "ms": "Manajemen dokumen dan pengingat perpanjangan"},
    "No documents yet.": {"zh": "还没有文件。", "ko": "아직 문서가 없습니다.", "ja": "書類はまだありません。", "id": "Belum ada dokumen.", "ms": "Belum ada dokumen."},
    "Search Documents": {"zh": "搜索文件", "ko": "문서 검색", "ja": "書類を検索", "id": "Cari Dokumen", "ms": "Cari Dokumen"},
    "Select Document": {"zh": "选择文件", "ko": "문서 선택", "ja": "書類を選択", "id": "Pilih Dokumen", "ms": "Pilih Dokumen"},
    "Untitled Document": {"zh": "无标题文件", "ko": "제목 없는 문서", "ja": "無題の書類", "id": "Dokumen Tanpa Judul", "ms": "Dokumen Tanpa Judul"},
    "Please enter document name.": {"zh": "请输入文件名称。", "ko": "문서명을 입력하세요.", "ja": "書類名を入力してください。", "id": "Silakan masukkan nama dokumen.", "ms": "Silakan masukkan nama dokumen."},
    "No attachment is available for this document.": {"zh": "此文件没有附件。", "ko": "이 문서에는 첨부파일이 없습니다.", "ja": "この書類には添付ファイルがありません。", "id": "Tidak ada lampiran untuk dokumen ini.", "ms": "Tidak ada lampiran untuk dokumen ini."},
    "Estimated Annual Fees": {"zh": "预估年度费用", "ko": "예상 연간 수수료", "ja": "推定年間費用", "id": "Perkiraan Biaya Tahunan", "ms": "Perkiraan Biaya Tahunan"},
    "End Date": {"zh": "结束日期", "ko": "종료일", "ja": "終了日", "id": "Tanggal Berakhir", "ms": "Tanggal Berakhir"},
    "Start Date": {"zh": "开始日期", "ko": "시작일", "ja": "開始日", "id": "Tanggal Mulai", "ms": "Tanggal Mulai"},
    "Renewal Cycle (Months)": {"zh": "续期周期（月）", "ko": "갱신 주기 (월)", "ja": "更新サイクル（月）", "id": "Siklus Perpanjangan (Bulan)", "ms": "Siklus Perpanjangan (Bulan)"},
    "Renewal cycle (months)": {"zh": "续期周期（月）", "ko": "갱신 주기 (월)", "ja": "更新サイクル（月）", "id": "Siklus perpanjangan (bulan)", "ms": "Siklus perpanjangan (bulan)"},
    "Remind Before (Months)": {"zh": "提前提醒（月）", "ko": "사전 알림 (월)", "ja": "事前リマインダー（月）", "id": "Ingatkan Sebelum (Bulan)", "ms": "Ingatkan Sebelum (Bulan)"},
    "Remind me before end date (months)": {"zh": "到期前提醒（月）", "ko": "종료일 전 알림 (월)", "ja": "終了日前にリマインド（月）", "id": "Ingatkan sebelum tanggal berakhir (bulan)", "ms": "Ingatkan sebelum tanggal berakhir (bulan)"},
    "Expiring Soon": {"zh": "即将到期", "ko": "곧 만료", "ja": "間もなく期限切れ", "id": "Segera Berakhir", "ms": "Segera Berakhir"},
    "Expiring in 30 Days": {"zh": "30天内到期", "ko": "30일 이내 만료", "ja": "30日以内に期限切れ", "id": "Berakhir dalam 30 Hari", "ms": "Berakhir dalam 30 Hari"},
    "Expired": {"zh": "已过期", "ko": "만료됨", "ja": "期限切れ", "id": "Kedaluwarsa", "ms": "Kedaluwarsa"},
    "Renew Soon": {"zh": "即将续期", "ko": "곧 갱신", "ja": "間もなく更新", "id": "Segera Perpanjang", "ms": "Segera Perpanjang"},
    "Valid": {"zh": "有效", "ko": "유효", "ja": "有効", "id": "Berlaku", "ms": "Berlaku"},
    "Upcoming Document Fees": {"zh": "即将到来的文件费用", "ko": "다가오는 문서 수수료", "ja": "今後の書類手数料", "id": "Biaya Dokumen Mendatang", "ms": "Biaya Dokumen Mendatang"},

    # ── Invoices ────────────────────────────────────────────────────────
    "Add Invoice": {"zh": "添加发票", "ko": "송장 추가", "ja": "請求書を追加", "id": "Tambah Faktur", "ms": "Tambah Faktur"},
    "Add a New Invoice": {"zh": "添加新发票", "ko": "새 송장 추가", "ja": "新しい請求書を追加", "id": "Tambah Faktur Baru", "ms": "Tambah Faktur Baru"},
    "Invoice": {"zh": "发票", "ko": "송장", "ja": "請求書", "id": "Faktur", "ms": "Faktur"},
    "Invoice Count": {"zh": "发票数量", "ko": "송장 수", "ja": "請求書数", "id": "Jumlah Faktur", "ms": "Jumlah Faktur"},
    "Invoice Status": {"zh": "发票状态", "ko": "송장 상태", "ja": "請求書ステータス", "id": "Status Faktur", "ms": "Status Faktur"},
    "Invoice Subtotal": {"zh": "发票小计", "ko": "송장 소계", "ja": "請求書小計", "id": "Subtotal Faktur", "ms": "Subtotal Faktur"},
    "Invoice Total": {"zh": "发票总计", "ko": "송장 합계", "ja": "請求書合計", "id": "Total Faktur", "ms": "Total Faktur"},
    "Invoice deleted.": {"zh": "发票已删除。", "ko": "송장이 삭제되었습니다.", "ja": "請求書を削除しました。", "id": "Faktur dihapus.", "ms": "Faktur dihapus."},
    "Manage Invoices": {"zh": "管理发票", "ko": "송장 관리", "ja": "請求書を管理", "id": "Kelola Faktur", "ms": "Kelola Faktur"},
    "Select Invoice": {"zh": "选择发票", "ko": "송장 선택", "ja": "請求書を選択", "id": "Pilih Faktur", "ms": "Pilih Faktur"},
    "Delete Invoice": {"zh": "删除发票", "ko": "송장 삭제", "ja": "請求書を削除", "id": "Hapus Faktur", "ms": "Hapus Faktur"},
    "Delete Invoice Permanently": {"zh": "永久删除发票", "ko": "송장 영구 삭제", "ja": "請求書を完全に削除", "id": "Hapus Faktur Secara Permanen", "ms": "Hapus Faktur Secara Permanen"},
    "Edit Invoice Details": {"zh": "编辑发票详情", "ko": "송장 상세 편집", "ja": "請求書詳細を編集", "id": "Edit Detail Faktur", "ms": "Edit Detail Faktur"},
    "Update Invoice Status": {"zh": "更新发票状态", "ko": "송장 상태 업데이트", "ja": "請求書ステータスを更新", "id": "Perbarui Status Faktur", "ms": "Perbarui Status Faktur"},
    "Current Invoices": {"zh": "当前发票", "ko": "현재 송장", "ja": "現在の請求書", "id": "Faktur Saat Ini", "ms": "Faktur Saat Ini"},
    "Open Invoice Inflow": {"zh": "未结发票流入", "ko": "미결 송장 유입", "ja": "未決済請求書の流入", "id": "Arus Masuk Faktur Terbuka", "ms": "Arus Masuk Faktur Terbuka"},
    "Could not delete invoice.": {"zh": "无法删除发票。", "ko": "송장을 삭제할 수 없습니다.", "ja": "請求書を削除できませんでした。", "id": "Tidak dapat menghapus faktur.", "ms": "Tidak dapat menghapus faktur."},
    "Issue Date": {"zh": "发行日期", "ko": "발행일", "ja": "発行日", "id": "Tanggal Terbit", "ms": "Tanggal Terbit"},
    "Issue": {"zh": "发行", "ko": "발행", "ja": "発行", "id": "Terbit", "ms": "Terbit"},
    "Draft": {"zh": "草稿", "ko": "초안", "ja": "下書き", "id": "Draf", "ms": "Draf"},
    "Sent": {"zh": "已发送", "ko": "발송됨", "ja": "送信済み", "id": "Terkirim", "ms": "Terkirim"},
    "Customer": {"zh": "客户", "ko": "고객", "ja": "顧客", "id": "Pelanggan", "ms": "Pelanggan"},
    "Customer Name": {"zh": "客户名称", "ko": "고객명", "ja": "顧客名", "id": "Nama Pelanggan", "ms": "Nama Pelanggan"},
    "Subtotal": {"zh": "小计", "ko": "소계", "ja": "小計", "id": "Subtotal", "ms": "Subtotal"},

    # ── Tax ──────────────────────────────────────────────────────────────
    "Tax Settings": {"zh": "税务设置", "ko": "세금 설정", "ja": "税金設定", "id": "Pengaturan Pajak", "ms": "Pengaturan Pajak"},
    "Tax Rate": {"zh": "税率", "ko": "세율", "ja": "税率", "id": "Tarif Pajak", "ms": "Tarif Pajak"},
    "Tax Rate Breakdown": {"zh": "税率明细", "ko": "세율 내역", "ja": "税率内訳", "id": "Rincian Tarif Pajak", "ms": "Rincian Tarif Pajak"},
    "Tax Rate For This Invoice %": {"zh": "此发票税率 %", "ko": "이 송장 세율 %", "ja": "この請求書の税率 %", "id": "Tarif Pajak untuk Faktur Ini %", "ms": "Tarif Pajak untuk Faktur Ini %"},
    "Tax Included": {"zh": "含税", "ko": "세금 포함", "ja": "税込", "id": "Termasuk Pajak", "ms": "Termasuk Pajak"},
    "Tax Name": {"zh": "税名", "ko": "세금 이름", "ja": "税金名", "id": "Nama Pajak", "ms": "Nama Pajak"},
    "Tax Notes": {"zh": "税务备注", "ko": "세금 메모", "ja": "税金メモ", "id": "Catatan Pajak", "ms": "Catatan Pajak"},
    "Tax Source": {"zh": "税源", "ko": "세금 출처", "ja": "税金ソース", "id": "Sumber Pajak", "ms": "Sumber Pajak"},
    "Tax Summary This Month": {"zh": "本月税务摘要", "ko": "이번 달 세금 요약", "ja": "今月の税金概要", "id": "Ringkasan Pajak Bulan Ini", "ms": "Ringkasan Pajak Bulan Ini"},
    "Tax Classification": {"zh": "税务分类", "ko": "세금 분류", "ja": "税金分類", "id": "Klasifikasi Pajak", "ms": "Klasifikasi Pajak"},
    "Tax Registration Number": {"zh": "税务登记号", "ko": "세금 등록 번호", "ja": "税務登録番号", "id": "Nomor Registrasi Pajak", "ms": "Nomor Registrasi Pajak"},
    "Tax Business Name": {"zh": "税务商户名", "ko": "세금 사업자명", "ja": "税務事業者名", "id": "Nama Bisnis Pajak", "ms": "Nama Bisnis Pajak"},
    "Tax Country Code": {"zh": "税务国家代码", "ko": "세금 국가 코드", "ja": "税金国コード", "id": "Kode Negara Pajak", "ms": "Kode Negara Pajak"},
    "Tax Calculation Method": {"zh": "税务计算方法", "ko": "세금 계산 방법", "ja": "税金計算方法", "id": "Metode Perhitungan Pajak", "ms": "Metode Perhitungan Pajak"},
    "Enable Tax Mode": {"zh": "启用税务模式", "ko": "세금 모드 활성화", "ja": "税金モードを有効化", "id": "Aktifkan Mode Pajak", "ms": "Aktifkan Mode Pajak"},
    "Default Rate": {"zh": "默认税率", "ko": "기본 세율", "ja": "デフォルト税率", "id": "Tarif Default", "ms": "Tarif Default"},
    "Default Tax Rate (%)": {"zh": "默认税率（%）", "ko": "기본 세율 (%)", "ja": "デフォルト税率 (%)", "id": "Tarif Pajak Default (%)", "ms": "Tarif Pajak Default (%)"},
    "Amount (Tax Included)": {"zh": "金额（含税）", "ko": "금액 (세금 포함)", "ja": "金額（税込）", "id": "Jumlah (Termasuk Pajak)", "ms": "Jumlah (Termasuk Pajak)"},
    "Amount Before Tax": {"zh": "税前金额", "ko": "세전 금액", "ja": "税前金額", "id": "Jumlah Sebelum Pajak", "ms": "Jumlah Sebelum Pajak"},
    "Amount Includes Tax": {"zh": "金额含税", "ko": "금액 세금 포함", "ja": "金額は税込", "id": "Jumlah Termasuk Pajak", "ms": "Jumlah Termasuk Pajak"},
    "Prices include tax": {"zh": "价格含税", "ko": "세금 포함 가격", "ja": "税込価格", "id": "Harga termasuk pajak", "ms": "Harga termasuk pajak"},
    "Invoice Entry Amount Includes Tax": {"zh": "发票金额含税", "ko": "송장 금액 세금 포함", "ja": "請求書金額は税込", "id": "Jumlah Entri Faktur Termasuk Pajak", "ms": "Jumlah Entri Faktur Termasuk Pajak"},
    "Manual Tax Edit For This Invoice": {"zh": "手动编辑此发票税务", "ko": "이 송장 세금 수동 편집", "ja": "この請求書の税金を手動編集", "id": "Edit Pajak Manual untuk Faktur Ini", "ms": "Edit Pajak Manual untuk Faktur Ini"},
    "Manual edit is locked while tax mode is off.": {"zh": "税务模式关闭时，手动编辑被锁定。", "ko": "세금 모드가 꺼져 있으면 수동 편집이 잠깁니다.", "ja": "税金モードがオフの間、手動編集はロックされています。", "id": "Edit manual terkunci saat mode pajak nonaktif.", "ms": "Edit manual terkunci saat mode pajak nonaktif."},
    "Open or close tax settings": {"zh": "打开或关闭税务设置", "ko": "세금 설정 열기/닫기", "ja": "税金設定を開く/閉じる", "id": "Buka atau tutup pengaturan pajak", "ms": "Buka atau tutup pengaturan pajak"},
    "Tax settings inside the invoice page": {"zh": "发票页面内的税务设置", "ko": "송장 페이지 내 세금 설정", "ja": "請求書ページ内の税金設定", "id": "Pengaturan pajak di halaman faktur", "ms": "Pengaturan pajak di halaman faktur"},
    "No tax-rate breakdown for this month.": {"zh": "本月没有税率明细。", "ko": "이번 달 세율 내역이 없습니다.", "ja": "今月の税率内訳はありません。", "id": "Tidak ada rincian tarif pajak bulan ini.", "ms": "Tidak ada rincian tarif pajak bulan ini."},
    "VAT": {"zh": "增值税", "ko": "부가세", "ja": "付加価値税", "id": "PPN", "ms": "PPN"},
    "Customer Tax No": {"zh": "客户税号", "ko": "고객 세금 번호", "ja": "顧客税番号", "id": "Nomor Pajak Pelanggan", "ms": "Nomor Pajak Pelanggan"},
    "Customer Tax No (Optional)": {"zh": "客户税号（可选）", "ko": "고객 세금 번호 (선택)", "ja": "顧客税番号（任意）", "id": "Nomor Pajak Pelanggan (Opsional)", "ms": "Nomor Pajak Pelanggan (Opsional)"},
    "Billing/Tax Email": {"zh": "账单/税务邮箱", "ko": "청구/세금 이메일", "ja": "請求/税金メール", "id": "Email Penagihan/Pajak", "ms": "Email Penagihan/Pajak"},
    "Project Tax Rate %": {"zh": "项目税率 %", "ko": "프로젝트 세율 %", "ja": "プロジェクト税率 %", "id": "Tarif Pajak Proyek %", "ms": "Tarif Pajak Proyek %"},
    "Use project-specific tax settings": {"zh": "使用项目专属税务设置", "ko": "프로젝트별 세금 설정 사용", "ja": "プロジェクト固有の税金設定を使用", "id": "Gunakan pengaturan pajak khusus proyek", "ms": "Gunakan pengaturan pajak khusus proyek"},
    "Source: Global default settings.": {"zh": "来源：全局默认设置。", "ko": "출처: 전역 기본 설정.", "ja": "ソース：グローバルデフォルト設定。", "id": "Sumber: Pengaturan default global.", "ms": "Sumber: Pengaturan default global."},
    "Source: Project-level tax override.": {"zh": "来源：项目级别税务覆盖。", "ko": "출처: 프로젝트 수준 세금 재정의.", "ja": "ソース：プロジェクトレベルの税金オーバーライド。", "id": "Sumber: Override pajak tingkat proyek.", "ms": "Sumber: Override pajak tingkat proyek."},
    "Project invoices use these values by default.": {"zh": "项目发票默认使用这些值。", "ko": "프로젝트 송장은 기본적으로 이 값을 사용합니다.", "ja": "プロジェクトの請求書はデフォルトでこれらの値を使用します。", "id": "Faktur proyek menggunakan nilai ini secara default.", "ms": "Faktur proyek menggunakan nilai ini secara default."},
    "Calculation Details": {"zh": "计算详情", "ko": "계산 상세", "ja": "計算詳細", "id": "Detail Perhitungan", "ms": "Detail Perhitungan"},
    "Estimate": {"zh": "预估", "ko": "추정", "ja": "見積", "id": "Perkiraan", "ms": "Perkiraan"},
    "Accrual": {"zh": "应计", "ko": "발생", "ja": "発生主義", "id": "Akrual", "ms": "Akrual"},
    "Cash": {"zh": "现金", "ko": "현금", "ja": "現金", "id": "Tunai", "ms": "Tunai"},
    "General Basis": {"zh": "一般基础", "ko": "일반 기준", "ja": "一般基準", "id": "Dasar Umum", "ms": "Dasar Umum"},
    "Quarterly": {"zh": "季度", "ko": "분기", "ja": "四半期", "id": "Kuartalan", "ms": "Kuartalan"},
    "Yearly": {"zh": "年度", "ko": "연간", "ja": "年次", "id": "Tahunan", "ms": "Tahunan"},
    "Report Type": {"zh": "报告类型", "ko": "보고서 유형", "ja": "レポートタイプ", "id": "Tipe Laporan", "ms": "Tipe Laporan"},
    "Review Frequency": {"zh": "审查频率", "ko": "검토 주기", "ja": "レビュー頻度", "id": "Frekuensi Tinjauan", "ms": "Frekuensi Tinjauan"},

    # ── Settings ────────────────────────────────────────────────────────
    "General": {"zh": "通用", "ko": "일반", "ja": "一般", "id": "Umum", "ms": "Umum"},
    "General Profile": {"zh": "通用档案", "ko": "일반 프로필", "ja": "一般プロファイル", "id": "Profil Umum", "ms": "Profil Umum"},
    "Language": {"zh": "语言", "ko": "언어", "ja": "言語", "id": "Bahasa", "ms": "Bahasa"},
    "User / Business Name": {"zh": "用户 / 商户名", "ko": "사용자 / 사업자명", "ja": "ユーザー / 事業者名", "id": "Nama Pengguna / Bisnis", "ms": "Nama Pengguna / Bisnis"},
    "Upload App Logo": {"zh": "上传应用logo", "ko": "앱 로고 업로드", "ja": "アプリロゴをアップロード", "id": "Unggah Logo Aplikasi", "ms": "Unggah Logo Aplikasi"},
    "Preview": {"zh": "预览", "ko": "미리보기", "ja": "プレビュー", "id": "Pratinjau", "ms": "Pratinjau"},
    "No uploaded logo.": {"zh": "未上传logo。", "ko": "업로드된 로고가 없습니다.", "ja": "ロゴがアップロードされていません。", "id": "Belum ada logo yang diunggah.", "ms": "Belum ada logo yang diunggah."},
    "Current Plan": {"zh": "当前套餐", "ko": "현재 플랜", "ja": "現在のプラン", "id": "Paket Saat Ini", "ms": "Paket Saat Ini"},
    "Privacy and Sync": {"zh": "隐私与同步", "ko": "개인정보 및 동기화", "ja": "プライバシーと同期", "id": "Privasi dan Sinkronisasi", "ms": "Privasi dan Sinkronisasi"},
    "Enable Cloud Sync (Optional)": {"zh": "启用云同步（可选）", "ko": "클라우드 동기화 활성화 (선택)", "ja": "クラウド同期を有効化（任意）", "id": "Aktifkan Sinkronisasi Cloud (Opsional)", "ms": "Aktifkan Sinkronisasi Cloud (Opsional)"},
    "Cloud Status": {"zh": "云端状态", "ko": "클라우드 상태", "ja": "クラウドステータス", "id": "Status Cloud", "ms": "Status Cloud"},
    "Cloud Account": {"zh": "云端账户", "ko": "클라우드 계정", "ja": "クラウドアカウント", "id": "Akun Cloud", "ms": "Akun Cloud"},
    "Cloud is currently off. You can enable it or export your data.": {"zh": "云端当前已关闭。您可以启用或导出数据。", "ko": "클라우드가 현재 꺼져 있습니다. 활성화하거나 데이터를 내보낼 수 있습니다.", "ja": "クラウドは現在オフです。有効にするかデータをエクスポートできます。", "id": "Cloud saat ini nonaktif. Anda dapat mengaktifkan atau mengekspor data.", "ms": "Cloud saat ini nonaktif. Anda dapat mengaktifkan atau mengekspor data."},
    "Cloud sync is active and the account is signed in.": {"zh": "云同步已激活，账户已登录。", "ko": "클라우드 동기화가 활성화되고 계정이 로그인되었습니다.", "ja": "クラウド同期がアクティブで、アカウントにサインインしています。", "id": "Sinkronisasi cloud aktif dan akun sudah masuk.", "ms": "Sinkronisasi cloud aktif dan akun sudah masuk."},
    "Last Sync": {"zh": "上次同步", "ko": "마지막 동기화", "ja": "最終同期", "id": "Sinkronisasi Terakhir", "ms": "Sinkronisasi Terakhir"},
    "No sync yet": {"zh": "尚未同步", "ko": "아직 동기화 없음", "ja": "まだ同期されていません", "id": "Belum ada sinkronisasi", "ms": "Belum ada sinkronisasi"},
    "Disabled": {"zh": "已禁用", "ko": "비활성", "ja": "無効", "id": "Nonaktif", "ms": "Nonaktif"},
    "Enabled": {"zh": "已启用", "ko": "활성", "ja": "有効", "id": "Aktif", "ms": "Aktif"},
    "Ready": {"zh": "就绪", "ko": "준비", "ja": "準備完了", "id": "Siap", "ms": "Siap"},
    "Setup Required": {"zh": "需要设置", "ko": "설정 필요", "ja": "セットアップが必要", "id": "Perlu Pengaturan", "ms": "Perlu Pengaturan"},
    "Connected": {"zh": "已连接", "ko": "연결됨", "ja": "接続済み", "id": "Terhubung", "ms": "Terhubung"},
    "Danger Zone": {"zh": "危险区域", "ko": "위험 구역", "ja": "危険ゾーン", "id": "Zona Bahaya", "ms": "Zona Bahaya"},
    "This Device Data": {"zh": "此设备数据", "ko": "이 기기 데이터", "ja": "このデバイスのデータ", "id": "Data Perangkat Ini", "ms": "Data Perangkat Ini"},
    "Export and Restore Data": {"zh": "导出与恢复数据", "ko": "데이터 내보내기 및 복원", "ja": "データのエクスポートと復元", "id": "Ekspor dan Pulihkan Data", "ms": "Ekspor dan Pulihkan Data"},
    "Delete Account Permanently": {"zh": "永久删除账户", "ko": "계정 영구 삭제", "ja": "アカウントを完全に削除", "id": "Hapus Akun Secara Permanen", "ms": "Hapus Akun Secara Permanen"},
    "Delete This Device Data": {"zh": "删除此设备数据", "ko": "이 기기 데이터 삭제", "ja": "このデバイスのデータを削除", "id": "Hapus Data Perangkat Ini", "ms": "Hapus Data Perangkat Ini"},
    "Delete My Cloud Data": {"zh": "删除我的云端数据", "ko": "내 클라우드 데이터 삭제", "ja": "クラウドデータを削除", "id": "Hapus Data Cloud Saya", "ms": "Hapus Data Cloud Saya"},
    "I understand account deletion is permanent": {"zh": "我理解账户删除是永久性的", "ko": "계정 삭제가 영구적임을 이해합니다", "ja": "アカウント削除が永久的であることを理解しています", "id": "Saya memahami penghapusan akun bersifat permanen", "ms": "Saya memahami penghapusan akun bersifat permanen"},
    "I understand restore replaces current data": {"zh": "我理解恢复会替换当前数据", "ko": "복원이 현재 데이터를 대체함을 이해합니다", "ja": "復元が現在のデータを置き換えることを理解しています", "id": "Saya memahami pemulihan menggantikan data saat ini", "ms": "Saya memahami pemulihan menggantikan data saat ini"},
    "This device data was deleted.": {"zh": "此设备数据已删除。", "ko": "이 기기 데이터가 삭제되었습니다.", "ja": "このデバイスのデータが削除されました。", "id": "Data perangkat ini telah dihapus.", "ms": "Data perangkat ini telah dihapus."},
    "Restore Backup Now": {"zh": "立即恢复备份", "ko": "지금 백업 복원", "ja": "今すぐバックアップを復元", "id": "Pulihkan Cadangan Sekarang", "ms": "Pulihkan Cadangan Sekarang"},
    "Choose JSON Data File": {"zh": "选择JSON数据文件", "ko": "JSON 데이터 파일 선택", "ja": "JSONデータファイルを選択", "id": "Pilih File Data JSON", "ms": "Pilih File Data JSON"},
    "Backup content is invalid.": {"zh": "备份内容无效。", "ko": "백업 내용이 유효하지 않습니다.", "ja": "バックアップ内容が無効です。", "id": "Konten cadangan tidak valid.", "ms": "Konten cadangan tidak valid."},
    "Backup restored successfully.": {"zh": "备份恢复成功。", "ko": "백업이 성공적으로 복원되었습니다.", "ja": "バックアップが正常に復元されました。", "id": "Cadangan berhasil dipulihkan.", "ms": "Cadangan berhasil dipulihkan."},
    "Invalid JSON file.": {"zh": "无效的JSON文件。", "ko": "유효하지 않은 JSON 파일.", "ja": "無効なJSONファイルです。", "id": "File JSON tidak valid.", "ms": "File JSON tidak valid."},
    "Advanced setup for developers": {"zh": "开发者高级设置", "ko": "개발자 고급 설정", "ja": "開発者向け高度な設定", "id": "Pengaturan lanjutan untuk pengembang", "ms": "Pengaturan lanjutan untuk pengembang"},
    "All summary cards are hidden in settings.": {"zh": "所有摘要卡片已在设置中隐藏。", "ko": "모든 요약 카드가 설정에서 숨겨져 있습니다.", "ja": "すべてのサマリーカードが設定で非表示になっています。", "id": "Semua kartu ringkasan disembunyikan di pengaturan.", "ms": "Semua kartu ringkasan disembunyikan di pengaturan."},

    # ── Auth ─────────────────────────────────────────────────────────────
    "Email": {"zh": "邮箱", "ko": "이메일", "ja": "メール", "id": "Email", "ms": "Email"},
    "Password": {"zh": "密码", "ko": "비밀번호", "ja": "パスワード", "id": "Kata Sandi", "ms": "Kata Sandi"},
    "Confirm Password": {"zh": "确认密码", "ko": "비밀번호 확인", "ja": "パスワード確認", "id": "Konfirmasi Kata Sandi", "ms": "Konfirmasi Kata Sandi"},
    "Sign In": {"zh": "登录", "ko": "로그인", "ja": "サインイン", "id": "Masuk", "ms": "Masuk"},
    "Sign Up": {"zh": "注册", "ko": "회원가입", "ja": "サインアップ", "id": "Daftar", "ms": "Daftar"},
    "Sign Out": {"zh": "退出", "ko": "로그아웃", "ja": "サインアウト", "id": "Keluar", "ms": "Keluar"},
    "Sign Out from Cloud": {"zh": "从云端退出", "ko": "클라우드에서 로그아웃", "ja": "クラウドからサインアウト", "id": "Keluar dari Cloud", "ms": "Keluar dari Cloud"},
    "Forgot Password": {"zh": "忘记密码", "ko": "비밀번호 찾기", "ja": "パスワードを忘れた場合", "id": "Lupa Kata Sandi", "ms": "Lupa Kata Sandi"},
    "Send Reset Link": {"zh": "发送重置链接", "ko": "재설정 링크 보내기", "ja": "リセットリンクを送信", "id": "Kirim Tautan Reset", "ms": "Kirim Tautan Reset"},
    "Please enter email and password.": {"zh": "请输入邮箱和密码。", "ko": "이메일과 비밀번호를 입력하세요.", "ja": "メールとパスワードを入力してください。", "id": "Silakan masukkan email dan kata sandi.", "ms": "Silakan masukkan email dan kata sandi."},
    "Please enter your email.": {"zh": "请输入您的邮箱。", "ko": "이메일을 입력하세요.", "ja": "メールアドレスを入力してください。", "id": "Silakan masukkan email Anda.", "ms": "Silakan masukkan email Anda."},
    "Password must be at least 6 characters.": {"zh": "密码至少需要6个字符。", "ko": "비밀번호는 최소 6자 이상이어야 합니다.", "ja": "パスワードは6文字以上必要です。", "id": "Kata sandi minimal 6 karakter.", "ms": "Kata sandi minimal 6 karakter."},
    "Passwords do not match.": {"zh": "密码不匹配。", "ko": "비밀번호가 일치하지 않습니다.", "ja": "パスワードが一致しません。", "id": "Kata sandi tidak cocok.", "ms": "Kata sandi tidak cocok."},
    "Signed in and data loaded.": {"zh": "已登录并加载数据。", "ko": "로그인 및 데이터 로드 완료.", "ja": "サインインしてデータを読み込みました。", "id": "Masuk dan data dimuat.", "ms": "Masuk dan data dimuat."},
    "Signed out.": {"zh": "已退出。", "ko": "로그아웃되었습니다.", "ja": "サインアウトしました。", "id": "Telah keluar.", "ms": "Telah keluar."},
    "Could not verify your account. Please try again.": {"zh": "无法验证您的账户。请重试。", "ko": "계정을 확인할 수 없습니다. 다시 시도하세요.", "ja": "アカウントを確認できませんでした。再度お試しください。", "id": "Tidak dapat memverifikasi akun Anda. Silakan coba lagi.", "ms": "Tidak dapat memverifikasi akun Anda. Silakan coba lagi."},
    "Remember sign-in on this device": {"zh": "在此设备上记住登录", "ko": "이 기기에서 로그인 기억", "ja": "このデバイスでサインインを記憶", "id": "Ingat masuk di perangkat ini", "ms": "Ingat masuk di perangkat ini"},
    "Load My Data": {"zh": "加载我的数据", "ko": "내 데이터 불러오기", "ja": "データを読み込み", "id": "Muat Data Saya", "ms": "Muat Data Saya"},
    "Your data was loaded from cloud.": {"zh": "您的数据已从云端加载。", "ko": "클라우드에서 데이터를 불러왔습니다.", "ja": "クラウドからデータを読み込みました。", "id": "Data Anda dimuat dari cloud.", "ms": "Data Anda dimuat dari cloud."},
    "Your data was saved to cloud.": {"zh": "您的数据已保存到云端。", "ko": "클라우드에 데이터를 저장했습니다.", "ja": "データをクラウドに保存しました。", "id": "Data Anda disimpan ke cloud.", "ms": "Data Anda disimpan ke cloud."},
    "Your cloud data was deleted.": {"zh": "您的云端数据已删除。", "ko": "클라우드 데이터가 삭제되었습니다.", "ja": "クラウドデータが削除されました。", "id": "Data cloud Anda telah dihapus.", "ms": "Data cloud Anda telah dihapus."},
    "Could not save changes.": {"zh": "无法保存更改。", "ko": "변경사항을 저장할 수 없습니다.", "ja": "変更を保存できませんでした。", "id": "Tidak dapat menyimpan perubahan.", "ms": "Tidak dapat menyimpan perubahan."},
    "Could not update status.": {"zh": "无法更新状态。", "ko": "상태를 업데이트할 수 없습니다.", "ja": "ステータスを更新できませんでした。", "id": "Tidak dapat memperbarui status.", "ms": "Tidak dapat memperbarui status."},
    "No new edits to save.": {"zh": "没有新的编辑需要保存。", "ko": "저장할 새 편집이 없습니다.", "ja": "保存する新しい編集はありません。", "id": "Tidak ada edit baru untuk disimpan.", "ms": "Tidak ada edit baru untuk disimpan."},
    "This name already exists.": {"zh": "此名称已存在。", "ko": "이 이름은 이미 존재합니다.", "ja": "この名前は既に存在します。", "id": "Nama ini sudah ada.", "ms": "Nama ini sudah ada."},
    "Enter amount greater than 0.": {"zh": "请输入大于0的金额。", "ko": "0보다 큰 금액을 입력하세요.", "ja": "0より大きい金額を入力してください。", "id": "Masukkan jumlah lebih dari 0.", "ms": "Masukkan jumlah lebih dari 0."},
    "Amount must be greater than zero.": {"zh": "金额必须大于零。", "ko": "금액은 0보다 커야 합니다.", "ja": "金額は0より大きくなければなりません。", "id": "Jumlah harus lebih dari nol.", "ms": "Jumlah harus lebih dari nol."},
    "Enable delete confirmation first.": {"zh": "请先启用删除确认。", "ko": "먼저 삭제 확인을 활성화하세요.", "ja": "まず削除確認を有効にしてください。", "id": "Aktifkan konfirmasi hapus terlebih dahulu.", "ms": "Aktifkan konfirmasi hapus terlebih dahulu."},

    # ── Attachments / Proof ──────────────────────────────────────────────
    "Attachment": {"zh": "附件", "ko": "첨부", "ja": "添付", "id": "Lampiran", "ms": "Lampiran"},
    "Attachment (Optional)": {"zh": "附件（可选）", "ko": "첨부 (선택)", "ja": "添付（任意）", "id": "Lampiran (Opsional)", "ms": "Lampiran (Opsional)"},
    "Attached": {"zh": "已附", "ko": "첨부됨", "ja": "添付済み", "id": "Terlampir", "ms": "Terlampir"},
    "Attach Invoice/Transaction Proof (Optional)": {"zh": "附上发票/交易证明（可选）", "ko": "송장/거래 증빙 첨부 (선택)", "ja": "請求書/取引証明を添付（任意）", "id": "Lampirkan Bukti Faktur/Transaksi (Opsional)", "ms": "Lampirkan Bukti Faktur/Transaksi (Opsional)"},
    "Attach Payment/Receipt Proof (Optional)": {"zh": "附上付款/收款证明（可选）", "ko": "결제/수금 증빙 첨부 (선택)", "ja": "支払い/入金証明を添付（任意）", "id": "Lampirkan Bukti Pembayaran/Penerimaan (Opsional)", "ms": "Lampirkan Bukti Pembayaran/Penerimaan (Opsional)"},
    "Attach Proof (Optional)": {"zh": "附上证明（可选）", "ko": "증빙 첨부 (선택)", "ja": "証明を添付（任意）", "id": "Lampirkan Bukti (Opsional)", "ms": "Lampirkan Bukti (Opsional)"},
    "Proof": {"zh": "证明", "ko": "증빙", "ja": "証明", "id": "Bukti", "ms": "Bukti"},
    "With Proof": {"zh": "有证明", "ko": "증빙 있음", "ja": "証明あり", "id": "Dengan Bukti", "ms": "Dengan Bukti"},
    "Without Proof": {"zh": "无证明", "ko": "증빙 없음", "ja": "証明なし", "id": "Tanpa Bukti", "ms": "Tanpa Bukti"},
    "Download Attachment": {"zh": "下载附件", "ko": "첨부 다운로드", "ja": "添付ファイルをダウンロード", "id": "Unduh Lampiran", "ms": "Unduh Lampiran"},
    "Download Invoice/Proof": {"zh": "下载发票/证明", "ko": "송장/증빙 다운로드", "ja": "請求書/証明をダウンロード", "id": "Unduh Faktur/Bukti", "ms": "Unduh Faktur/Bukti"},
    "Download CSV": {"zh": "下载CSV", "ko": "CSV 다운로드", "ja": "CSVをダウンロード", "id": "Unduh CSV", "ms": "Unduh CSV"},
    "Download PDF": {"zh": "下载PDF", "ko": "PDF 다운로드", "ja": "PDFをダウンロード", "id": "Unduh PDF", "ms": "Unduh PDF"},

    # ── Misc types / categories ──────────────────────────────────────────
    "Fixed": {"zh": "固定", "ko": "고정", "ja": "固定", "id": "Tetap", "ms": "Tetap"},
    "Variable": {"zh": "可变", "ko": "변동", "ja": "変動", "id": "Variabel", "ms": "Variabel"},
    "Recurring": {"zh": "定期", "ko": "정기", "ja": "定期", "id": "Berulang", "ms": "Berulang"},
    "Recurring Planned": {"zh": "计划定期", "ko": "계획 정기", "ja": "計画定期", "id": "Berulang Terencana", "ms": "Berulang Terencana"},
    "Manual": {"zh": "手动", "ko": "수동", "ja": "手動", "id": "Manual", "ms": "Manual"},
    "Other": {"zh": "其他", "ko": "기타", "ja": "その他", "id": "Lainnya", "ms": "Lainnya"},
    "None": {"zh": "无", "ko": "없음", "ja": "なし", "id": "Tidak Ada", "ms": "Tidak Ada"},
    "Not set": {"zh": "未设置", "ko": "미설정", "ja": "未設定", "id": "Belum diatur", "ms": "Belum diatur"},
    "Unknown": {"zh": "未知", "ko": "알 수 없음", "ja": "不明", "id": "Tidak Diketahui", "ms": "Tidak Diketahui"},
    "All": {"zh": "全部", "ko": "전체", "ja": "すべて", "id": "Semua", "ms": "Semua"},
    "Global": {"zh": "全局", "ko": "전역", "ja": "グローバル", "id": "Global", "ms": "Global"},
    "ID": {"zh": "编号", "ko": "ID", "ja": "ID", "id": "ID", "ms": "ID"},
    "Rate": {"zh": "比率", "ko": "비율", "ja": "レート", "id": "Tarif", "ms": "Tarif"},
    "Starts this month": {"zh": "本月开始", "ko": "이번 달 시작", "ja": "今月開始", "id": "Mulai bulan ini", "ms": "Mulai bulan ini"},
    "Example: Perfumes": {"zh": "示例：香水", "ko": "예시: 향수", "ja": "例：香水", "id": "Contoh: Parfum", "ms": "Contoh: Parfum"},

    # ── Analysis insights ────────────────────────────────────────────────
    "Financial position is under control": {"zh": "财务状况处于控制中", "ko": "재무 상황이 통제되고 있습니다", "ja": "財務状況はコントロールされています", "id": "Posisi keuangan terkendali", "ms": "Posisi keuangan terkendali"},
    "The situation is nearly balanced between commitments and expected income.": {"zh": "承诺与预期收入之间几乎平衡。", "ko": "약정과 예상 수입 사이가 거의 균형을 이루고 있습니다.", "ja": "コミットメントと予想収入がほぼ均衡しています。", "id": "Situasi hampir seimbang antara komitmen dan pendapatan yang diharapkan.", "ms": "Situasi hampir seimbang antara komitmen dan pendapatan yang diharapkan."},
    "There is a current coverage gap that needs follow-up.": {"zh": "目前存在覆盖缺口，需要跟进。", "ko": "현재 커버리지 갭이 있어 후속 조치가 필요합니다.", "ja": "現在カバレッジギャップがあり、フォローアップが必要です。", "id": "Ada kesenjangan cakupan saat ini yang perlu ditindaklanjuti.", "ms": "Ada kesenjangan cakupan saat ini yang perlu ditindaklanjuti."},
    "Future coverage is positive after collection.": {"zh": "收款后未来覆盖为正。", "ko": "수금 후 향후 커버리지가 양수입니다.", "ja": "回収後の将来カバレッジはプラスです。", "id": "Cakupan masa depan positif setelah penagihan.", "ms": "Cakupan masa depan positif setelah penagihan."},
    "Current Expense": {"zh": "当前支出", "ko": "현재 지출", "ja": "現在の支出", "id": "Pengeluaran Saat Ini", "ms": "Pengeluaran Saat Ini"},

    # ── Inline Panel & Dialog ────────────────────────────────────────────
    "Inline Panel": {"zh": "内嵌面板", "ko": "인라인 패널", "ja": "インラインパネル", "id": "Panel Inline", "ms": "Panel Inline"},
    "This Streamlit version does not support dialog, so an inline form is shown instead.": {"zh": "此Streamlit版本不支持对话框，已改用内嵌表单。", "ko": "이 Streamlit 버전은 대화상자를 지원하지 않아 인라인 양식이 표시됩니다.", "ja": "このStreamlitバージョンはダイアログをサポートしていないため、インラインフォームが表示されます。", "id": "Versi Streamlit ini tidak mendukung dialog, jadi formulir inline ditampilkan.", "ms": "Versi Streamlit ini tidak mendukung dialog, jadi formulir inline ditampilkan."},

}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_lang_code() -> str:
    """Return the ISO-639 code for the currently active language."""
    lang_name = st.session_state.get("settings", {}).get("language", "العربية")
    return LANGUAGES.get(lang_name, "ar")


def is_rtl() -> bool:
    """True when the active language reads right-to-left."""
    lang_name = st.session_state.get("settings", {}).get("language", "العربية")
    return lang_name in RTL_LANGUAGES


def get_months() -> list[str]:
    """Return month names for the current language."""
    return MONTHS.get(get_lang_code(), MONTHS["en"])


def make_t() -> Callable[[str, str], str]:
    """Build a translator for the current session language.

    Returns a callable with the legacy ``t(ar, en)`` signature.
    For Arabic and English the positional arguments are returned directly.
    For all other languages the *en* text is looked up in ``_TRANSLATIONS``.
    """
    lang_name = st.session_state.get("settings", {}).get("language", "العربية")
    code = LANGUAGES.get(lang_name, "ar")

    if code == "ar":
        return lambda ar, en: ar
    if code == "en":
        return lambda ar, en: en

    def _translate(ar: str, en: str) -> str:
        entry = _TRANSLATIONS.get(en)
        if entry and code in entry:
            return entry[code]
        return en  # fallback to English

    return _translate

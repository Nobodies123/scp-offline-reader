from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from jnius import autoclass
import sqlite3

WebView = autoclass("android.webkit.WebView")
WebViewClient = autoclass("android.webkit.WebViewClient")
PythonActivity = autoclass("org.kivy.android.PythonActivity")


class BrowserScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"

        # 添加顶部工具栏
        self.toolbar = BoxLayout(size_hint_y=None, height=50)
        self.add_widget(self.toolbar)

        self.url_input = TextInput(size_hint_x=0.8, multiline=False)
        self.url_input.bind(on_text_validate=self.on_enter_url)
        self.toolbar.add_widget(self.url_input)

        self.back_button = Button(text="后退", size_hint_x=0.1)
        self.back_button.bind(on_release=self.go_back)
        self.toolbar.add_widget(self.back_button)

        self.forward_button = Button(text="前进", size_hint_x=0.1)
        self.forward_button.bind(on_release=self.go_forward)
        self.toolbar.add_widget(self.forward_button)

        self.home_button = Button(text="主页", size_hint_x=0.1)
        self.home_button.bind(on_release=self.go_home)
        self.toolbar.add_widget(self.home_button)

        # 添加WebView
        self.webview = WebView(PythonActivity.mActivity)
        self.webview.getSettings().setJavaScriptEnabled(True)
        self.webview.setWebViewClient(WebViewClient())
        self.add_widget(self.webview)

        # 连接到SQLite数据库
        self.connection = sqlite3.connect("local_db.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS web_content (
                url TEXT PRIMARY KEY,
                content TEXT
            )
        """
        )
        self.connection.commit()

        self.home_url = "https://example.com"
        self.load_url(self.home_url)

    def load_url(self, url):
        self.url_input.text = url
        self.cursor.execute("SELECT content FROM web_content WHERE url=?", (url,))
        row = self.cursor.fetchone()
        if row:
            content = row[0]
            self.webview.loadData(content, "text/html", "utf-8")
        else:
            self.webview.loadUrl(url)
            self.webview.setWebViewClient(WebViewClient())
            self.webview.setWebViewClient(self.CustomWebViewClient(self))

    def on_enter_url(self, instance):
        self.load_url(instance.text)

    def go_back(self, instance):
        if self.webview.canGoBack():
            self.webview.goBack()

    def go_forward(self, instance):
        if self.webview.canGoForward():
            self.webview.goForward()

    def go_home(self, instance):
        self.load_url(self.home_url)

    class CustomWebViewClient(WebViewClient):
        def __init__(self, browser_screen):
            self.browser_screen = browser_screen

        def onPageFinished(self, view, url):
            if self.browser_screen.should_cache_url(url):
                view.evaluateJavascript(
                    "(function() { return document.documentElement.outerHTML; })();",
                    self.browser_screen.save_page_content(url),
                )

    def save_page_content(self, url):
        def callback(content):
            self.cursor.execute(
                "INSERT OR REPLACE INTO web_content (url, content) VALUES (?, ?)",
                (url, content),
            )
            self.connection.commit()

        return callback

    def should_cache_url(self, url):
        # 在这里定义URL是否满足条件的逻辑
        return True


class MyApp(App):
    def build(self):
        return BrowserScreen()


if __name__ == "__main__":
    MyApp().run()

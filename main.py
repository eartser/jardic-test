import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

URL = 'http://www.jardic.ru/index_r.htm'

LANG_TITLE_DICT = {
    'r': 'Японско-русский словарь онлайн Jardic',
    'j': 'ロシア語・英語・中国語オンライン辞書 - Jardic辞書',
    'e': 'Japanese-Russian, Japanese-English online dictionary Jardic',
}
LANGS = list(LANG_TITLE_DICT.keys())

DICT_R_TITLES_DICT = {
    'dic_jardic': 'Jardic',
    'dic_edict': 'Edict',
    'dic_tatoeba': 'Tatoeba',
    'dic_warodai': 'Warodai',
    'dic_enamdict': 'Enamdict',
    'dic_chekhov': 'Чехов',
    'dic_yarxi': 'ЯРКСИ',
    'dic_kanjidic': 'Kanjdic',
    'dic_stories': 'Stories',
    'dic_bkrs': 'БКРС',
    'dic_unihan': 'Unihan',
    'dic_japaneselaw': 'Laws of Japan',
    'dic_medic': 'Medic',
}
DICTS = list(DICT_R_TITLES_DICT.keys())


class TestJardic:

    def setup_class(self):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 2)

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.driver.get(URL)
        yield

    def teardown_class(self):
        self.driver.close()

    def find_element(self, by, value):
        return self.wait.until(ec.visibility_of_element_located((by, value)))

    def find_elements(self, by, value):
        return self.wait.until(ec.visibility_of_all_elements_located((by, value)))

    def get_language_button(self, lang):
        lang_button = self.find_element(By.XPATH, f"//a[@href='index_{lang}.htm']")
        return lang_button

    def search(self, word):
        search_box = self.find_element(By.NAME, 'q')
        search_box.click()
        search_box.send_keys(word)
        search_button = self.find_element(By.XPATH, "//input[@type='submit']")
        search_button.click()

    def select_dicts(self, selected_dicts):
        for dic in DICTS:
            dict_checkbox = self.find_element(By.NAME, dic)
            if (dic in selected_dicts and not dict_checkbox.is_selected()) \
                    or (dic not in selected_dicts and dict_checkbox.is_selected()):
                dict_checkbox.click()

    def go_to_page(self, page_number):
        page_button = self.find_element(By.XPATH, f"//span[@class='blk']/a[contains(text(), '{page_number}')]")
        page_button.click()

    def get_result_dicts(self, all_pages=False):
        result_dicts = []
        counter = 1

        if not all_pages:
            return [dic.text for dic in self.find_elements(By.XPATH, f"//table[@id='tabContent']/tbody/tr//a")]

        while True:
            result_dicts += [dic.text for dic in self.find_elements(By.XPATH, f"//table[@id='tabContent']/tbody/tr//a")]
            try:
                self.go_to_page(counter + 1)
            except TimeoutException:
                break
            counter += 1
        return result_dicts

    def count_results(self, all_pages=False):
        return len(self.get_result_dicts(all_pages))

    # tests

    def test_lang_available(self):
        for lang in LANGS:
            lang_button = self.get_language_button(lang)
            lang_button.click()

    def test_lang_changeable(self):
        for lang, title in LANG_TITLE_DICT.items():
            lang_button = self.get_language_button(lang)
            lang_button.click()
            assert title in self.driver.title

    def test_first_load_dicts(self):
        for dic in DICTS:
            dic_checkbox = self.find_element(By.NAME, dic)
            assert not dic_checkbox.is_selected()

    def test_first_load_search(self):
        self.search('en')
        result_dicts = self.get_result_dicts(all_pages=True)
        assert list(set(result_dicts)) == ['Jardic']

    def test_search_with_selected_dicts(self):
        selected_dicts = DICTS[5:6]
        self.select_dicts(selected_dicts)
        self.search('en')
        result_dicts = self.get_result_dicts(all_pages=True)
        selected_dicts = [DICT_R_TITLES_DICT[d] for d in selected_dicts]
        for result_dict in result_dicts:
            assert result_dict in selected_dicts

    def test_page_limit(self):
        selected_dicts = DICTS[:6]
        self.select_dicts(selected_dicts)
        self.search('marui')
        all_res_cnt = self.count_results(all_pages=True)
        last_page_res_cnt = self.count_results()
        assert last_page_res_cnt == all_res_cnt % 20

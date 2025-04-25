import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import pyperclip
import asyncio
import aiohttp
import re
import html
import json

class SpellChecker:
    @staticmethod
    async def check_with_daum(text):
        """다음 맞춤법 검사기 호출"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://dic.daum.net',
            'Referer': 'https://dic.daum.net/grammar_checker.do',
        }

        url = 'https://dic.daum.net/grammar_checker.do'

        data = {
            'sentence': text
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status != 200:
                    return {'error': f'HTTP 오류: {response.status}'}

                try:
                    content = await response.text()

                    # 결과 영역 찾기
                    result_div = re.search(r'<div class="cont_spell">(.*?)</div>\s*</div>\s*</div>', content, re.DOTALL)
                    if not result_div:
                        return {'error': '맞춤법 검사 결과를 찾을 수 없습니다.'}

                    html_content = result_div.group(1)

                    # 결과 텍스트를 저장할 리스트
                    result_parts = []
                    error_count = 0

                    # HTML 파싱
                    pos = 0
                    while pos < len(html_content):
                        # <span> 태그 찾기 (일반 텍스트)
                        span_match = re.search(r'<span>(.*?)</span>', html_content[pos:], re.DOTALL)

                        # <a> 태그 찾기 (오류가 있는 부분)
                        a_match = re.search(r'<a [^>]*data-error-input="([^"]*)" data-error-output="([^"]*)"[^>]*>', html_content[pos:], re.DOTALL)

                        # <br> 태그 찾기 (줄바꿈)
                        br_match = re.search(r'<br/>', html_content[pos:], re.DOTALL)

                        # 가장 먼저 나오는 태그 처리
                        if span_match and (not a_match or span_match.start() < a_match.start()) and (not br_match or span_match.start() < br_match.start()):
                            # 일반 텍스트
                            content_text = html.unescape(span_match.group(1)).strip()
                            if content_text:
                                result_parts.append(content_text)
                            pos += span_match.end()

                        elif a_match and (not br_match or a_match.start() < br_match.start()):
                            # 오류가 있는 부분
                            error_input = html.unescape(a_match.group(1)).strip()
                            error_output = html.unescape(a_match.group(2)).strip()

                            # 원본 단어(교정된 단어) 형식으로 추가
                            if error_input != error_output:
                                result_parts.append(f"{error_input}({error_output})")
                                error_count += 1
                            else:
                                result_parts.append(error_input)

                            # </a> 태그까지 건너뛰기
                            end_a_pos = html_content.find('</a>', pos + a_match.end())
                            if end_a_pos != -1:
                                pos = end_a_pos + 4
                            else:
                                pos += a_match.end()

                        elif br_match:
                            # 줄바꿈
                            result_parts.append("\n")
                            pos += br_match.end()

                        else:
                            # 더 이상 처리할 태그가 없으면 종료
                            break

                    # 결과 조합
                    checked_text = ' '.join(result_parts).replace(' \n ', '\n').strip()

                    return {
                        'checked': checked_text,
                        'errors': error_count,
                        'original': text
                    }

                except Exception as e:
                    import traceback
                    print(f"Error parsing Daum result: {traceback.format_exc()}")
                    return {'error': f'응답 처리 중 오류: {str(e)}'}

    @staticmethod
    async def check_with_pusan(text):
        """부산대 맞춤법 검사기 호출"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        url = "http://speller.cs.pusan.ac.kr/results"

        data = {
            'text1': text,
            'btnModeChange': 'on'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, ssl=False) as response:
                    if response.status != 200:
                        return {'error': f'HTTP 오류: {response.status}'}

                    response_text = await response.text(encoding='utf-8')

                    # JavaScript data 변수 추출
                    data_match = re.search(r'data = (\[.*?\]);', response_text, re.DOTALL)
                    if not data_match:
                        return {'error': '맞춤법 검사 결과를 찾을 수 없습니다.'}

                    data_json = data_match.group(1)

                    try:
                        # JSON 형식으로 파싱
                        try:
                            data = json.loads(data_json)
                        except json.JSONDecodeError:
                            data_json = data_json.replace("'", '"')
                            data = json.loads(data_json)

                        if not data:
                            return {'error': '맞춤법 검사 결과가 비어있습니다.'}

                        # 첫 번째 항목
                        first_item = data[0]
                        errors = first_item.get('errInfo', [])

                        # 원본 텍스트에서 오류를 찾아 교체
                        result_text = text
                        replaced_positions = []  # 이미 교체된 위치 추적

                        # 오류 정보 정렬
                        sorted_errors = sorted(errors, key=lambda x: len(x.get('orgStr', '')), reverse=True)  # 긴 문자열부터 처리

                        for error in sorted_errors:
                            org_str = error.get('orgStr', '')
                            cand_word = error.get('candWord', '')

                            if not org_str or not cand_word or org_str == cand_word:
                                continue

                            print(f"처리 중: '{org_str}' -> '{cand_word}'")

                            # 원본 텍스트에서 모든 일치하는 부분 찾기
                            matches = list(re.finditer(re.escape(org_str), result_text))

                            if not matches:
                                print(f"  - 일치하는 문자열을 찾을 수 없음: '{org_str}'")
                                continue

                            # 이미 교체되지 않은 첫 번째 일치 부분 선택
                            valid_match = None
                            for match in matches:
                                is_replaced = False
                                for start, end in replaced_positions:
                                    if not (match.end() <= start or match.start() >= end):  # 겹침 확인
                                        is_replaced = True
                                        break
                                if not is_replaced:
                                    valid_match = match
                                    break

                            if valid_match:
                                start, end = valid_match.span()
                                replacement = f"{org_str}({cand_word})"

                                # 해당 부분 교체
                                result_text = result_text[:start] + replacement + result_text[end:]

                                # 교체된 위치 기록 (위치 조정 필요)
                                offset = len(replacement) - (end - start)
                                replaced_positions = [(s + offset if s >= end else s, e + offset if e >= end else e) for s, e in replaced_positions]
                                replaced_positions.append((start, start + len(replacement)))

                                print(f"  - 교체 성공: '{org_str}' -> '{replacement}' (위치: {start}-{end})")
                            else:
                                print(f"  - 모든 일치 부분이 이미 교체됨: '{org_str}'")

                        return {
                            'checked': result_text,
                            'errors': len(errors),
                            'original': text
                        }

                    except Exception as e:
                        import traceback
                        print(f"결과 처리 중 오류: {traceback.format_exc()}")
                        return {'error': f'결과 처리 중 오류: {str(e)}'}

        except Exception as e:
            import traceback
            print(f"요청 중 오류: {traceback.format_exc()}")
            return {'error': f'요청 중 오류: {str(e)}'}

class SpellCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("한글 맞춤법 검사기")
        self.root.geometry("800x800")  # 창 크기 키움

        # 클립보드 이전 값 저장
        self.prev_clipboard = pyperclip.paste()

        # 클립보드 모니터링 상태와 타이머 ID
        self.clipboard_monitoring = True
        self.after_id = None

        self.setup_ui()

        # 클립보드 감시 시작
        self.start_clipboard_monitoring()

    def setup_ui(self):
        # 설명 레이블
        info_label = tk.Label(self.root, text="텍스트를 입력하거나 붙여넣기 하세요. 클립보드에 복사된 텍스트는 자동으로 불러옵니다.")
        info_label.pack(pady=5)

        # 원본 텍스트 영역
        original_frame = tk.Frame(self.root)
        original_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(original_frame, text="원본 텍스트:").pack(anchor='w')

        self.original_text = scrolledtext.ScrolledText(original_frame, height=8)
        self.original_text.pack(fill=tk.BOTH, expand=True)

        # 버튼 영역
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # 검사 버튼
        self.check_button = tk.Button(button_frame, text="맞춤법 검사", command=self.start_spell_check)
        self.check_button.pack(side=tk.LEFT, padx=10)

        # 복사 및 초기화 버튼 프레임
        copy_clear_frame = tk.Frame(button_frame)
        copy_clear_frame.pack(side=tk.LEFT, padx=5)

        # 다음 복사 버튼
        self.copy_daum_button = tk.Button(copy_clear_frame, text="다음 결과 복사", command=lambda: self.copy_result("daum"), state=tk.DISABLED)
        self.copy_daum_button.grid(row=0, column=0, padx=2)

        # 부산대 복사 버튼
        self.copy_pusan_button = tk.Button(copy_clear_frame, text="부산대 결과 복사", command=lambda: self.copy_result("pusan"), state=tk.DISABLED)
        self.copy_pusan_button.grid(row=0, column=1, padx=2)

        # 초기화 버튼
        self.clear_button = tk.Button(button_frame, text="초기화", command=self.clear_text)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # 클립보드 모니터링 토글 체크박스
        self.clipboard_var = tk.BooleanVar(value=True)
        self.clipboard_check = tk.Checkbutton(button_frame, text="클립보드 자동 감지",
                                              variable=self.clipboard_var,
                                              command=self.toggle_clipboard_monitoring)
        self.clipboard_check.pack(side=tk.LEFT, padx=10)

        # 결과 텍스트 영역 (탭으로 구분)
        result_frame = ttk.Notebook(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 다음 결과 탭
        daum_frame = tk.Frame(result_frame)
        result_frame.add(daum_frame, text="다음 맞춤법 검사 결과")

        # 다음 결과 텍스트 영역
        self.daum_result_text = scrolledtext.ScrolledText(daum_frame, height=10)
        self.daum_result_text.pack(fill=tk.BOTH, expand=True)

        # 부산대 결과 탭
        pusan_frame = tk.Frame(result_frame)
        result_frame.add(pusan_frame, text="부산대 맞춤법 검사 결과")

        # 부산대 결과 텍스트 영역
        self.pusan_result_text = scrolledtext.ScrolledText(pusan_frame, height=10)
        self.pusan_result_text.pack(fill=tk.BOTH, expand=True)

        # 상태 표시줄
        self.status_label = tk.Label(self.root, text="준비", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def toggle_clipboard_monitoring(self):
        """클립보드 모니터링 켜기/끄기"""
        self.clipboard_monitoring = self.clipboard_var.get()

        if self.clipboard_monitoring:
            self.status_label.config(text="클립보드 자동 감지 활성화")
            self.start_clipboard_monitoring()
        else:
            self.status_label.config(text="클립보드 자동 감지 비활성화")
            self.stop_clipboard_monitoring()

    def start_clipboard_monitoring(self):
        """클립보드 모니터링 시작"""
        if self.clipboard_monitoring:
            self.check_clipboard()

    def stop_clipboard_monitoring(self):
        """클립보드 모니터링 중지"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def check_clipboard(self):
        """클립보드 내용 주기적으로 확인"""
        if not self.clipboard_monitoring:
            return

        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != self.prev_clipboard:
                self.prev_clipboard = current_clipboard
                if current_clipboard.strip():
                    self.original_text.delete("1.0", tk.END)
                    self.original_text.insert("1.0", current_clipboard)
                    self.status_label.config(text="클립보드 내용이 불러와졌습니다")
        except Exception:
            pass  # 클립보드 오류 무시

        # 1초마다 반복 확인 (지정된 주기로 유지)
        self.after_id = self.root.after(1000, self.check_clipboard)

    def start_spell_check(self):
        """맞춤법 검사 시작 - 비동기 함수를 별도 스레드에서 실행"""
        text = self.original_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("경고", "검사할 텍스트를 입력하세요.")
            return

        self.check_button.config(state=tk.DISABLED)
        self.status_label.config(text="맞춤법 검사 중...")
        self.root.update_idletasks()

        # 별도 스레드에서 비동기 함수 실행
        thread = threading.Thread(target=self.run_async_check, args=(text,))
        thread.daemon = True
        thread.start()

    def run_async_check(self, text):
        """별도 스레드에서 비동기 맞춤법 검사 실행 (두 검사기 동시에)"""
        async def async_check_both():
            try:
                # 두 맞춤법 검사기를 동시에 실행
                daum_task = asyncio.create_task(SpellChecker.check_with_daum(text))
                pusan_task = asyncio.create_task(SpellChecker.check_with_pusan(text))

                # 모든 태스크가 완료될 때까지 대기
                daum_result, pusan_result = await asyncio.gather(daum_task, pusan_task)

                return {
                    'daum': daum_result,
                    'pusan': pusan_result
                }
            except Exception as e:
                import traceback
                print(f"Error details: {traceback.format_exc()}")
                return {'error': str(e)}

        # 새 이벤트 루프 생성 및 비동기 함수 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(async_check_both())
            # GUI 업데이트는 메인 스레드에서 해야 함
            self.root.after(0, lambda: self.update_results(results))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            loop.close()
            # 버튼 활성화는 메인 스레드에서
            self.root.after(0, lambda: self.check_button.config(state=tk.NORMAL))

    def update_results(self, results):
        """맞춤법 검사 결과를 GUI에 표시"""
        if 'error' in results:
            self.show_error(results['error'])
            return

        # 다음 결과 표시
        daum_result = results.get('daum', {})
        if 'error' in daum_result:
            self.daum_result_text.delete("1.0", tk.END)
            self.daum_result_text.insert("1.0", f"오류: {daum_result['error']}")
        else:
            daum_checked_text = daum_result.get('checked', '')
            daum_errors_count = daum_result.get('errors', 0)

            self.daum_result_text.delete("1.0", tk.END)
            self.daum_result_text.insert("1.0", daum_checked_text)
            self.copy_daum_button.config(state=tk.NORMAL)

        # 부산대 결과 표시
        pusan_result = results.get('pusan', {})
        if 'error' in pusan_result:
            self.pusan_result_text.delete("1.0", tk.END)
            self.pusan_result_text.insert("1.0", f"오류: {pusan_result['error']}")
        else:
            pusan_checked_text = pusan_result.get('checked', '')
            pusan_errors_count = pusan_result.get('errors', 0)

            self.pusan_result_text.delete("1.0", tk.END)
            self.pusan_result_text.insert("1.0", pusan_checked_text)
            self.copy_pusan_button.config(state=tk.NORMAL)

        # 상태 표시
        daum_errors = daum_result.get('errors', 0) if 'error' not in daum_result else '오류'
        pusan_errors = pusan_result.get('errors', 0) if 'error' not in pusan_result else '오류'
        self.status_label.config(text=f"검사 완료: 다음({daum_errors}개 오류), 부산대({pusan_errors}개 오류)")

    def show_error(self, error_msg):
        """오류 메시지 표시"""
        self.status_label.config(text=f"오류 발생")
        messagebox.showerror("오류", f"맞춤법 검사 중 오류가 발생했습니다: {error_msg}")
        self.check_button.config(state=tk.NORMAL)

    def copy_result(self, source):
        """결과를 클립보드에 복사"""
        if source == "daum":
            result = self.daum_result_text.get("1.0", tk.END).strip()
            source_name = "다음"
        else:  # "pusan"
            result = self.pusan_result_text.get("1.0", tk.END).strip()
            source_name = "부산대"

        if result:
            pyperclip.copy(result)
            self.status_label.config(text=f"{source_name} 결과가 클립보드에 복사되었습니다")

    def clear_text(self):
        """텍스트 필드 초기화"""
        self.original_text.delete("1.0", tk.END)
        self.daum_result_text.delete("1.0", tk.END)
        self.pusan_result_text.delete("1.0", tk.END)
        self.status_label.config(text="준비")
        self.copy_daum_button.config(state=tk.DISABLED)
        self.copy_pusan_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpellCheckerApp(root)
    root.mainloop()

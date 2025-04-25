import aiohttp
import asyncio
import json
import re
import html

class NaraSpellChecker:
    @staticmethod
    async def check_with_nara(text):
        """부산대 맞춤법 검사기 호출 - 직접 폼 제출 방식"""
        # 실제 브라우저의 헤더 정보를 최대한 유사하게 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="91", " Not;A Brand";v="99", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document'
        }

        # 다이렉트로 results 페이지에 폼 제출
        url = "http://speller.cs.pusan.ac.kr/results"  # http 사용 (https가 아님)

        # 폼 데이터 준비
        data = {
            'text1': text,
            'btnModeChange': 'off'  # "강한 규칙 적용하기" 체크됨
        }

        try:
            print("부산대 맞춤법 검사 요청 보내는 중...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, ssl=False) as response:
                    print(f"응답 상태 코드: {response.status}")

                    if response.status != 200:
                        return {'error': f'HTTP 오류: {response.status}'}

                    result_html = await response.text()
                    print(f"응답 데이터 길이: {len(result_html)} 바이트")

                    # 결과 파싱
                    return NaraSpellChecker.parse_pnu_result(result_html, text)

        except Exception as e:
            import traceback
            print(f"오류 발생: {traceback.format_exc()}")
            return {'error': f'요청 중 오류: {str(e)}'}

    @staticmethod
    def parse_pnu_result(result_html, original_text):
        """부산대 맞춤법 검사기 결과 파싱 - JavaScript data 변수 사용"""
        try:
            # JavaScript data 변수 추출
            data_match = re.search(r'data = (\[.*?\]);', result_html, re.DOTALL)
            if not data_match:
                print("JavaScript data 변수를 찾을 수 없습니다.")
                return {'error': '맞춤법 검사 결과를 찾을 수 없습니다.'}

            data_json = data_match.group(1)
            print("JavaScript data 변수를 찾았습니다.")

            try:
                # JSON 형식으로 파싱
                data = json.loads(data_json)
                print(f"데이터 구조: {json.dumps(data[:1], ensure_ascii=False, indent=2)}")

                if not data:
                    return {'error': '맞춤법 검사 결과가 비어있습니다.'}

                # 첫 번째 항목(일반적으로 한 번에 하나의 맞춤법 검사만 있음)
                first_item = data[0]
                orig_str = first_item.get('str', '')
                errors = first_item.get('errInfo', [])

                print(f"원본 문자열: {orig_str}")
                print(f"오류 개수: {len(errors)}")

                # 오류 정보를 이용한 결과 조합
                result_parts = []
                last_pos = 0

                # 정렬된 오류 목록
                sorted_errors = sorted(errors, key=lambda x: x.get('start', 0))

                for error in sorted_errors:
                    start = error.get('start', 0)
                    end = error.get('end', 0)
                    org_str = error.get('orgStr', '')
                    cand_word = error.get('candWord', '')

                    # 오류 전의 텍스트 추가
                    if start > last_pos:
                        result_parts.append(orig_str[last_pos:start])

                    # 오류 부분 추가 - 원본(교정) 형식
                    if org_str and cand_word and org_str != cand_word:
                        result_parts.append(f"{org_str}({cand_word})")
                    else:
                        result_parts.append(org_str)

                    last_pos = end

                # 마지막 오류 이후의 텍스트 추가
                if last_pos < len(orig_str):
                    result_parts.append(orig_str[last_pos:])

                # 최종 결과 조합
                final_text = ''.join(result_parts)

                return {
                    'checked': final_text,
                    'errors': len(errors),
                    'original': original_text
                }

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {str(e)}")
                return {'error': f'JSON 파싱 오류: {str(e)}'}

        except Exception as e:
            import traceback
            print(f"HTML 파싱 중 오류: {traceback.format_exc()}")
            return {'error': f'HTML 파싱 중 오류: {str(e)}'}

# 테스트 코드
async def test_nara_spellcheck():
    print("=== 부산대 맞춤법 검사 테스트 시작 ===")
    text = '''사람들 참 이기적이지 않나?\n\n자기가 사는 동네에 공원과 산, 강, 자연이 있길 바라면서\n벌레와 야생동물은 있어선 안 되고\n\n거리가 항상 깨끗하길 바라면서\n환경미화원은 눈에 띄는 시간에 일해선 안 되고

택배는 365일 24시간 빨리 받아야하면서
택배노동자들의 땀냄새는 더럽고 불쾌하고
'''
    result = await NaraSpellChecker.check_with_nara(text)
    print("\n=== 부산대 맞춤법 검사 결과 ===")
    if 'error' in result:
        print(f"오류: {result['error']}")
    else:
        print(f"원본: {result['original']}")
        print(f"교정: {result['checked']}")
        print(f"오류 개수: {result['errors']}")
    print("=============================")

# 테스트 실행
if __name__ == "__main__":
    asyncio.run(test_nara_spellcheck())

import fitz  # PyMuPDF
import io
from PIL import Image
import os
import base64
import requests
import tarfile
import re
import io
import openai
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def parse_pdf(file_path):
    result = {
        'text': '',
        'images': [],
        'tables': []
    }

    doc = fitz.open(file_path)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1

        text = page.get_text()
        if text:
            result['text'] += f'{text}'

        try:
            pix = page.get_pixmap()
            image = Image.open(io.BytesIO(pix.tobytes()))
            result['images'].append({
                'page': page_num,
                'image': image
            })
        except Exception as e:
            print(f"페이지 이미지 변환 오류 (페이지 {page_num}): {e}")

    return result


def upload_img(prompt, img_url_list, messages):
    messages += [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
        ],
    }]
    for img_url in img_url_list:
        messages[0]["content"].append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_url}",
                },
            }
        )

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        max_tokens=16384,
    )
    return response.choices[0].message.content, messages


def download_arxiv_files(url, download_dir='downloads'):
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    import re
    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)(v\d+)?', url)
    if not match:
        print("유효한 arXiv URL이 아닙니다.")
        return None, None, None

    arxiv_id = match.group(1)
    version = match.group(2) if match.group(2) else ''
    arxiv_id_full = arxiv_id + version

    pdf_url = f'https://arxiv.org/pdf/{arxiv_id_full}.pdf'
    pdf_response = requests.get(pdf_url)
    pdf_path = os.path.join(download_dir, f'{arxiv_id_full}.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_response.content)
    print(f'PDF 파일 다운로드 완료: {pdf_path}')

    src_url = f'https://arxiv.org/src/{arxiv_id_full}'
    src_response = requests.get(src_url, stream=True)
    if src_response.status_code != 200:
        print("이 논문은 TeX 소스 파일을 제공하지 않습니다.")
        return pdf_path, None, arxiv_id_full

    src_tar_path = os.path.join(download_dir, f'{arxiv_id_full}_src.tar.gz')
    with open(src_tar_path, 'wb') as f:
        for chunk in src_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print(f'TeX 소스 파일 다운로드 완료: {src_tar_path}')

    tex_project_dir = os.path.join(download_dir, f'{arxiv_id_full}_src')
    if not os.path.exists(tex_project_dir):
        os.makedirs(tex_project_dir)

    with tarfile.open(src_tar_path, 'r:gz') as tar:
        tar.extractall(path=tex_project_dir)
    print(f'TeX 프로젝트 폴더 생성 완료: {tex_project_dir}')

    os.remove(src_tar_path)

    return pdf_path, tex_project_dir, arxiv_id_full

async def proc_paper_pdf(url, channel):
    pdf_path, tex_folder_path, paper_id = download_arxiv_files(url)
    ret = parse_pdf(pdf_path)
    for x in ret['text'].split('\n'):
        print(x)

    base64_list = []
    for ii, xx in enumerate(ret['images']):
        x = xx['image']
        x.save(f"temp_paper/{ii}.png")
        base64_image = encode_image(f"temp_paper/{ii}.png")
        base64_list.append(base64_image)

    print()
    print()
    print()
    prompt = f"""다음 논문 내용을 분석 및 정리를 해줘.
    논문의 내용은 다음과 같아: {ret['text']}
    그리고 논문의 각 페이지를 스크린샷 찍은 이미지들을 첨부할게.
    수식과 테이블과 이미지는 이 스크린샷을 통해 확인해줘.
    해당 표랑 그림이 Table이나 Fig 라는 이름으로 본문에 등장할텐데 어디에서 어떤 의미로 어떻게 쓰였는지 유의해줘.
    너가 출력해야할 내용은 다음과 같아.
    1. 논문 전체의 내용 요약: 무슨 논문이고, 어떤 문제를 풀었고, 어떤 아이디어와 방법론을 썼고, 기존과의 차별점이나 기여한건 무엇이고, 성능이 얼마나 개선됐는지 실험결과를 요약해줘.
    단순히 Abstract나 Introduction을 요약하기만 하면 안 되고 논문 전체의 내용에 대한 요약이 돼야해. 이것만 읽어도 이 논문이 무슨 내용인지 알 수 있어야 하고 자세히 읽을지 말지 판단할 수 있어야해.
    2. 섹션별로 요약: 각 섹션마다, 또 각 섹션에 서브섹션이 있을텐데 각각에 대해 내용을 요약해줘. 섹션 별로 아무리 적어도 3~4문장은 돼야해. 디테일을 너무 생략하지 말고 한국어로 번역하는 김에 가볍게 요약도 한다는 느낌으로 살짝만 요약하고 되도록이면 원문의 디테일을 놓치지 말아줘. 충분히 자세하게 적어줘.
    2-1. Result나 Exeperiment 섹션의 경우 구체적인 수치를 함께 언급해줘. 성능이 정량적으로 얼마나 나아졌는지 함께 적어줘.
    3. 각 표랑 그림이 논문의 어디에 등장하고 어떤 의미가 있는지 적어줘.
    4. 이 논문이 인용한 논문들 중 자주 언급하는 논문이 있거나 주제와 관련해서 중요도가 높아보이는 논문이 있으면 따로 언급해줘.
    5. 여기까지 읽고 나서 내가 궁금해 할 법한 질문이나 더 알고 싶어할 것 같은 디테일에 대해 예상 질문을 5개 이상 만들고 각각에 대한 답변을 미리 달아놔줘.
    일단 여기까지 답변한 다음에 그 이후 대화에서 내가 이 논문에 대한 질문들을 할거야.
    그러면 논문에서 정확히 어느 부분에 해당하는지 근거를 들어가면서 답변을 해주면 돼. 답변을 할 때 논문에 명시적으로 나온 내용이면 해당 문장을 인용해서 출처를 달아주고, 네가 임의로 답변할때는 "논문에 나온 내용은 아니지만" 이라든가 "제 생각에는" 같은 말로 별도로 명시해줘.
    한국어로 적되, 그냥 번역하면 번역투라 이해하기 힘드니깐 네가 한국어로 자연스럽게 이해하기 쉽게 paraphrasing 다시 해줘."""
    ret, messages = upload_img(prompt, base64_list, [])
    print(ret)

    for i in range(0, len(ret), 1990):
        await channel.send(ret[i:i+1990])
    return messages

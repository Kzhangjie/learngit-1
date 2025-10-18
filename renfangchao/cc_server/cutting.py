import re
import uuid
from typing import Callable, List

# from define.common import clip_message
# from tencentcloud.common.http.pre_conn import logger
from utils import getLogger
import os

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])


class Cutter(object):
    def __init__(self):
        self.ellipses = "......"
        self.sp_keys = []
        self.key_to_msg = {}

    def _set_uuid_msg(self, text):
        key = f"<{str(uuid.uuid4())}>"
        self.sp_keys.append(key)
        self.key_to_msg[key] = text
        return key

    #  移除无用换行
    def _remove_link_break(self, text: str) -> str:
        return text.replace("\n\n", "\n")

    #  移除无用链接
    def _remove_deep_link(self, text: str) -> str:
        return re.sub(r"\[\^\d]", "", text)

    #  精简代码
    def _remove_code(self, text: str) -> str:
        code_block_pattern = r"(```.*?\n```)"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for match in matches:
            match: str
            code_lines = match.strip().splitlines()
            code_lines = [s for s in code_lines if s]
            new_code_msg = match
            if len(code_lines) > 5:
                new_code_msg = f"""{code_lines[0]}
    {code_lines[1]}
    {self.ellipses}
    {code_lines[-2]}
    {code_lines[-1]}"""
            key = self._set_uuid_msg(new_code_msg)
            text = text.replace(match, key)
        return text

    def _easier_table(self, table: List[str]) -> str:
        head_over = False
        head = []
        contents = []
        cell_count = 0
        for table_line in table:
            if ("|-") in table_line:
                cell_count = table_line.count("|-")
                head_over = True
                head.append(table_line)
                continue
            if not head_over:
                head.append(table_line)
                continue
            contents.append(table_line)
        if len(contents) > 2:
            ellipses_msg = f"|{self.ellipses}" * cell_count + "|"
            contents = [contents[0], ellipses_msg, contents[-1]]
        msg1 = "\n".join(head)
        msg2 = "\n".join(contents)
        return f"{msg1}\n{msg2}"

    def _check_table(self, table: List[str]) -> bool:
        have_table_info = False
        for table_line in table:
            if "|-" in table_line:
                have_table_info = True
        if len(table) < 3 or not have_table_info:
            return False
        return True

    # 精简表格
    def _remove_table(self, text: str) -> str:
        table = []
        for line in text.splitlines():
            if line.startswith("|"):
                table.append(line)
                continue
            if not self._check_table(table):
                table = []
                continue
            new_table = self._easier_table(table)
            if len(new_table) > 0:
                key = self._set_uuid_msg(new_table)
                text = text.replace("\n".join(table), key)
            table = []

        if self._check_table(table):
            new_table = self._easier_table(table)
            if len(new_table) > 0:
                key = self._set_uuid_msg(new_table)
                text = text.replace("\n".join(table), key)
        return text

    # 精简正文内容
    def _sp_key_in_text(self, text):
        for key in self.sp_keys:
            if key in text:
                return True
        return False

    # 从中间开始遍历
    def _traverse_from_middle(self, arr):
        n = len(arr)
        middle = n // 2
        if n % 2 == 1:
            yield arr[middle]
            for i in range(middle):
                yield arr[middle + i + 1]
                yield arr[middle - i - 1]
            return
        for i in range(middle):
            yield arr[middle + i]
            yield arr[middle - i - 1]

    def _split_sentence(self, text: str):
        split_word = "。"
        if "。" not in text:
            split_word = "."
        msgs = text.split(split_word)
        new_msgs = []
        for index, msg in enumerate(msgs):
            if len(msg) <= 0:
                continue
            if index != len(msgs) - 1:
                new_msgs.append(f"{msg}{split_word}")
            else:
                new_msgs.append(msg)
        return new_msgs

    def _handle_body_content(self, text: str):
        title_with_hash = re.compile(r"^#{1,6}\s+.+$")
        # 标题保留
        if title_with_hash.match(text):
            return text
        sentences = self._split_sentence(text)
        keep_msg = []
        for sentence in sentences:
            # 保留第一句
            if len(keep_msg) <= 0:
                keep_msg.append(sentence)
                continue
            # 保留加粗或斜体
            if sentence.count("*") >= 2:
                keep_msg.append(sentence)
        return "".join(keep_msg)

    def _remove_less_important_content(self, text: str):
        all_paragraph = text.splitlines()
        all_paragraph = [s for s in all_paragraph if s]
        for paragraph in self._traverse_from_middle(all_paragraph):
            if self._sp_key_in_text(paragraph):
                continue
            new_text = self._handle_body_content(paragraph)
            key = self._set_uuid_msg(new_text)
            text = text.replace(paragraph, key)
            return text, True
        return text, False

    def _get_real_output(self, text: str):
        for key, content in self.key_to_msg.items():
            text = text.replace(key, content)
        return text

    def _hardcode_len(self, text: str, target_len: int):
        middle = target_len // 2
        return text[:middle] + f"\n{self.ellipses}\n" + text[-middle:]

    def _reduce(self, text: str, target_len: int = 2000):
        if len(text) <= target_len:
            return text
        normal_remove_function: List[Callable[[str], str]] = [
            self._remove_link_break,
            self._remove_deep_link,
            self._remove_code,
            self._remove_table,
        ]
        escape_text = text
        for function in normal_remove_function:
            escape_text = function(escape_text)
            text = self._get_real_output(escape_text)
            if len(text) <= target_len:
                return text
        while True:
            escape_text, have_next = self._remove_less_important_content(escape_text)
            if not have_next:
                break
            text = self._get_real_output(escape_text)
            if len(text) <= target_len:
                return text
        text = self._get_real_output(escape_text)
        return self._hardcode_len(text, target_len)

    def reduce(self, text: str, target_len: int = 2000) -> str:
        try:
            return self._reduce(text, target_len)
        except Exception as e:
            logger.info(f"origin text: {text}")
            logger.error(f"<ALERT> cutting failed. err: {e}")
            return self.clip_message(text)

    def clip_message(self, content: str, max_length: int = 2000) -> str:
        """裁剪消息，如果超过 max_length 则删去中间的用 ... 代替"""
        if len(content) <= max_length:
            return content
        logger.warning(
            f"content_length exceeds. max_length {max_length}. content: {content}"
        )
        half_length = max_length // 2
        return content[:half_length] + "..." + content[-half_length:]


def cutting(text: str, target_len: int = 2000) -> str:
    cutter = Cutter()
    return cutter.reduce(text, target_len)


if __name__ == "__main__":
    # 示例Markdown内容
    markdown_content = "# 鲁迅：文学巨匠与思想先驱 \n## 鲁迅生平与时代背景\n### 早年生活与求学经历\n#### 家庭背景与童年生活\n* 鲁迅，原名周树人，1881年9月25日出生于浙江绍兴的一个没落士大夫家庭。父亲周伯宜是秀才，母亲鲁瑞是大家闺秀。鲁迅的童年在绍兴度过，家境虽不富裕，但家庭氛围较为开明。\n#### 私塾与新式学堂\n* 鲁迅幼年在家乡的私塾接受传统教育，学习四书五经等经典。1898年，他进入南京水师学堂学习，后转入江南陆师学堂附设的矿路学堂，开始接触新学。\n#### 留学日本\n* 1902年，鲁迅赴日本留学，先后在东京弘文学院和仙台医学专门学校学习。在日本期间，他受到西方思想的影响，开始关注社会问题和文学创作。\n#### 回国后的工作与生活\n* 1909年，鲁迅回国，先后在杭州、绍兴等地任教。1912年，他应蔡元培之邀，赴北京教育部任职，开始了他的文学创作生涯。\n\n### 时代背景与社会环境\n#### 清末民初的社会动荡\n* 鲁迅生活的时代正值清末民初，社会动荡不安。辛亥革命推翻了清朝统治，但随之而来的军阀混战和社会腐败使得国家陷入困境。\n#### 新文化运动的兴起\n* 1915年，陈独秀创办《新青年》杂志，标志着新文化运动的兴起。鲁迅积极参与其中，发表了一系列批判封建礼教和旧文化的文章，成为新文化运动的重要代表人物。\n#### 五四运动的影响\n* 1919年，五四运动爆发，鲁迅积极投身其中，支持学生运动，倡导民主与科学。五四运动进一步激发了他的创作热情，推动了他的思想转变。\n\n### 文学创作与思想转变\n#### 早期文学创作\n* 鲁迅的早期文学创作以小说和散文为主，代表作有《狂人日记》、《阿Q正传》等。这些作品揭露了封建社会的黑暗和人性的扭曲，表达了他对旧社会的批判和对新生活的向往。\n#### 思想启蒙与社会批判\n* 在新文化运动和五四运动的影响下，鲁迅的思想逐渐从启蒙主义转向社会批判。他开始关注社会问题，批判封建礼教和旧文化，倡导民主与科学。\n#### 文学风格的转变\n* 随着思想的转变，鲁迅的文学风格也发生了变化。他的作品从早期的批判现实主义逐渐转向后期的讽刺与幽默，创作手法更加成熟，语言更加犀利。\n\n\n## 鲁迅的文学成就\n### 小说创作与代表作\n#### 《狂人日记》\n* 《狂人日记》是鲁迅的第一篇白话小说，发表于1918年。这部作品通过一个“狂人”的视角，揭示了封建社会的“吃人”本质，表达了作者对封建礼教的强烈批判。\n#### 《阿Q正传》\n* 《阿Q正传》发表于1921年，是鲁迅最著名的代表作之一。小说通过阿Q这个典型人物，讽刺了当时中国社会的种种弊病，尤其是国民性的弱点。\n#### 《呐喊》与《彷徨》\n* 《呐喊》和《彷徨》是鲁迅的两部重要小说集，分别发表于1923年和1926年。这两部作品收录了鲁迅早期的许多重要小说，如《狂人日记》、《孔乙己》、《药》等，集中体现了鲁迅对封建社会的批判和对新生活的向往。\n\n### 散文与杂文\n#### 《朝花夕拾》\n* 《朝花夕拾》是鲁迅的一部散文集，发表于1926年。这部作品通过回忆童年和青少年时期的生活，展现了作者对故乡和亲人的深厚感情，同时也表达了他对旧社会的批判。\n#### 《野草》\n* 《野草》是鲁迅的一部散文诗集，发表于1927年。这部作品以象征主义的手法，表达了对现实社会的深刻思考和对未来的希望。\n#### 杂文创作\n* 鲁迅的杂文创作贯穿其一生，数量众多，内容广泛。他的杂文以犀利的语言和深刻的洞察力，批判了当时社会的种种弊病，倡导民主与科学，成为中国现代杂文的典范。\n\n### 翻译与文学批评\n#### 翻译作品\n* 鲁迅一生翻译了大量外国文学作品，包括俄国文学、日本文学和西方文学等。他的翻译作品不仅丰富了中国现代文学的内容，也促进了中国文学与世界文学的交流。\n#### 文学批评\n* 鲁迅在文学批评方面也有重要贡献。他撰写了许多文学评论文章，对中国现代文学的发展提出了许多建设性的意见。他的批评文章以犀利的语言和深刻的洞察力，对当时文坛的种种现象进行了深刻的剖析。\n#### 对外国文学的借鉴\n* 鲁迅在创作中广泛借鉴了外国文学的技巧和手法。他的小说和散文在结构、语言和表现手法上，都受到了外国文学的深刻影响。这使得他的作品在艺术上具有独特的风格和魅力。\n\n\n## 鲁迅的思想与影响\n### 思想启蒙与社会批判\n#### 启蒙思想的形成\n* 鲁迅的启蒙思想深受西方文化影响，他在日本留学期间接触了达尔文、尼采等人的思想，逐渐形成了自己的启蒙观念。他主张通过教育唤醒民众，推动社会进步。\n#### 对封建礼教的批判\n* 鲁迅在多部作品中深刻批判了封建礼教对人性的压制，如《狂人日记》中对“吃人”礼教的揭露，以及《阿Q正传》中对国民劣根性的讽刺。他的批判不仅限于文学，更是对社会现实的深刻反思。\n#### 社会批判的深度与广度\n* 鲁迅的社会批判不仅限于封建礼教，还涉及社会腐败、官僚主义、愚昧无知等多个方面。他的杂文如《论雷峰塔的倒掉》、《记念刘和珍君》等，深刻揭示了当时社会的种种弊病，展现了他作为思想先驱的深刻洞察力。\n\n### 对中国文学的影响\n#### 开创白话文小说先河\n* 鲁迅是中国现代白话文小说的奠基人之一，他的《狂人日记》是中国第一篇白话文小说，开创了中国现代小说的新纪元。他的作品语言简洁有力，结构新颖，对后世作家产生了深远影响。\n#### 推动现实主义文学发展\n* 鲁迅的创作始终坚持现实主义原则，他的作品如《阿Q正传》、《药》等，深刻反映了当时中国的社会现实，揭示了人性的复杂与社会的黑暗，推动了中国现实主义文学的发展。\n#### 文学批评的贡献\n* 鲁迅在文学批评方面也有重要贡献，他撰写了大量评论文章，对中国现代文学的发展提出了许多建设性的意见。他的批评文章以犀利的语言和深刻的洞察力，对当时文坛的种种现象进行了深刻的剖析。\n\n### 对后世作家的启示\n#### 坚持独立思考与批判精神\n* 鲁迅的思想和创作始终贯穿着独立思考与批判精神，他不盲从权威，敢于挑战传统观念。这种精神对后世作家产生了深远影响，激励他们勇于探索和创新。\n#### 关注社会现实与人民生活\n* 鲁迅的作品始终关注社会现实和人民生活，他的创作灵感来源于对社会的深刻观察和思考。这种关注现实的创作态度对后世作家具有重要的启示意义。\n#### 文学语言的创新与突破\n* 鲁迅在文学语言上进行了大胆的创新与突破，他的作品语言简洁有力，富有表现力。这种语言风格对后世作家产生了深远影响，推动了中国现代文学语言的发展。\n\n\n## 鲁迅的文化遗产\n### 鲁迅纪念馆与研究机构\n#### 北京鲁迅博物馆\n* 北京鲁迅博物馆成立于1956年，是中国最早建立的鲁迅纪念馆之一。馆内收藏了大量鲁迅的手稿、书籍和生活用品，全面展示了鲁迅的生平和创作历程。\n#### 上海鲁迅纪念馆\n* 上海鲁迅纪念馆位于上海市虹口区，成立于1951年。纪念馆坐落在鲁迅故居旁，展示了鲁迅在上海的生活和工作情况，并设有专门的展览和研究区域。\n#### 绍兴鲁迅纪念馆\n* 绍兴鲁迅纪念馆位于鲁迅的故乡浙江绍兴，成立于1953年。纪念馆包括鲁迅故居、百草园和三味书屋等景点，生动再现了鲁迅的童年和青少年时期的生活环境。\n#### 鲁迅研究机构\n* 国内外有多家专门研究鲁迅的学术机构，如中国鲁迅研究会、日本鲁迅研究会等。这些机构定期举办学术研讨会，出版研究刊物，推动鲁迅研究的发展。\n\n### 鲁迅作品在当代的传播\n#### 鲁迅作品的再版与翻译\n* 鲁迅的作品在中国和世界各地不断再版，并被翻译成多种语言。中文版鲁迅全集多次修订再版，英文版、日文版、俄文版等也相继问世，使得鲁迅的思想和文学成就得以广泛传播。\n#### 鲁迅作品在教育中的地位\n* 鲁迅的作品被广泛编入中国中小学语文教材，如《狂人日记》、《阿Q正传》、《故乡》等经典篇目，成为学生必读的内容。这不仅有助于学生了解鲁迅的思想和文学成就，也培养了他们的批判性思维。\n#### 鲁迅作品在影视作品中的呈现\n* 鲁迅的作品多次被改编成电影、电视剧和舞台剧，如《阿Q正传》、《药》、《祝福》等。这些影视作品通过视觉艺术的形式，将鲁迅的文学世界生动地呈现给观众，进一步扩大了其影响力。\n#### 鲁迅作品在网络平台上的传播\n* 随着互联网的发展，鲁迅的作品在各大网络平台上广泛传播。许多网站和应用程序提供鲁迅作品的电子版，方便读者随时随地阅读。同时，社交媒体上也涌现出大量关于鲁迅的讨论和研究文章，促进了鲁迅思想的传播。\n\n### 鲁迅精神的现代意义\n#### 批判精神与独立思考\n* 鲁迅的批判精神和对独立思考的倡导在当代社会仍然具有重要意义。在信息爆炸的时代，保持独立思考和批判精神，勇于质疑和反思，是每个公民应具备的基本素质。\n#### 社会责任感与担当\n* 鲁迅始终关注社会现实和人民生活，他的作品充满了对社会的责任感和担当精神。在当代社会，这种精神激励着人们关注社会问题，积极参与社会公益事业，为社会的进步贡献力量。\n#### 文化传承与创新\n* 鲁迅在文学创作和文化传承方面做出了巨大贡献，他的作品和思想是中国现代文化的重要组成部分。在全球化背景下，继承和发扬鲁迅的精神，推动文化创新，是实现中华民族伟大复兴的重要途径。\n\n\n"
    print(len(markdown_content))
    print(markdown_content)
    print("-------------------------------------------")

    new_msg = Cutter().reduce(markdown_content, 2000)
    print(new_msg)
    print(len(new_msg))

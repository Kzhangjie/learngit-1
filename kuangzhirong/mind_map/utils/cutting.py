import re
import uuid
from typing import Callable, List

# from define.common import clip_message
# from tencentcloud.common.http.pre_conn import logger
import logging
logger = logging.getLogger("tencentcloud_sdk_common")


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
            return clip_message(text)
    def clip_message(content: str, max_length: int = 2000) -> str:
        """裁剪消息，如果超过 max_length 则删去中间的用 ... 代替"""
        if len(content) <= max_length:
            return content
        logger.warning(
            f"content_length exceeds. max_length {max_length}. content: {content}"
        )
        half_length = max_length // 2
        return content[:half_length] + "..." + content[-half_length:]



if __name__ == "__main__":
    # 示例Markdown内容
    markdown_content = """标题：月光下的誓言\n\n在一个静谧的小镇，春风温柔地拂过每一处角落，带起阵阵花香，这个小镇名叫月牙湾，因为它的形状就像一弯新月。在这个小镇的东南角，有一座小屋，屋里住着一个名叫李晨的男子。他是一名诗人，性情温和，眼中常含笑意，心中藏着一腔柔情。\n\n李晨的诗在小镇上颇有名气，许多人慕名而来求取他的诗作。然而，他的心早已被一个女孩所占据，那个女孩名叫云裳，是镇上花店老板的女儿，她的笑容如同春日里的阳光，温暖而明媚。\n\n李晨与云裳的相遇就像是一场命中注定的邂逅。那天，李晨带着一本未完成的诗稿去云裳家的花店买花。当他走进花店，被那绚烂的色彩和芬芳的花香所吸引时，他第一次看见了云裳。她正细心地为一束玫瑰点缀上绿色的叶子，动作轻柔，如同春风拂过水面。\n\n云裳抬眼望见了李晨，微笑着问：“先生，您需要些什么？”那微笑如同夜空中最亮的星辰，深深地刻在了李晨的心中。他心跳加速，声音有些颤抖地回答：“我想要一束能代表春天的花。”\n\n云裳轻盈地在花店中穿梭，最终为他挑选了一束带有露珠的白色百合和几朵粉嫩的桃花。她把花束递给李晨时，他们的手指不经意间触碰，那一刻，仿佛时间都静止了。\n\n从那以后，李晨几乎每天都会去那家花店，有时是为了买花，有时仅仅是为了看一眼云裳。他开始为云裳写下许多诗篇，诗中充满了对云裳的爱慕与渴望。\n\n春去夏来，小镇的风也变得热烈起来。一天傍晚，李晨鼓起勇气向云裳表白了心迹。他们在月牙湾边，坐在一块大石头上，星空作证，海浪低语。李晨拿起云裳的手，轻声说道：“云裳，你是我生命中最美的诗。我愿用我的全部才华和一生的时间，只为书写一个关于你的故事。”\n\n云裳的眼睛里闪着泪光，她感受到了李晨话语中那份深沉的爱意。她轻轻点头，两人的心在那一刻紧紧相连。月光下，他们的誓言如同那些夜空中最亮的星星，永远照耀着他们的爱情之路。\n\n然而，美好的时光总是短暂的。不久后，云裳的父亲因为生意的缘故，决定举家搬迁到远方的城市。这对于沉浸在爱情甜蜜中的李晨和云裳来说，无疑是个沉重的打击。分别的那天，李晨将一本装订精致的诗集交到云裳手中，那是他为她写的所有诗歌，也是他无法用言语表达的爱恋。\n\n云裳含着泪，紧紧抱住李晨，说道：“晨，无论我们相隔多远，我的心都会与你同在。请你等我，等我回来。”\n\n之后的岁月里，李晨每天都在月牙湾边等待着云裳的归来，每天都在写着新的诗篇，希望有一天能够亲手交给她。他相信，就像他诗中所写的那样——\n\n“纵使千山万水，也不能阻隔\n两颗真心的相守\n月光下的誓言，永不褪色。”\n\n直到有一天，一封从远方寄来的信，带来了云裳的消息，以及她即将归来的消息。李晨站在月牙湾边，心中充满了期待与欢喜，他知道，他的爱情将如初升的月亮，再次圆满。\n\n这个故事告诉我们，爱情就像李晨的诗篇，它超越了时间和距离的限制，它需要耐心、信任和承诺。而真正的爱，就像月光一样，即使在最黑暗的夜晚，也能照亮彼此的心房。"""
    print(len(markdown_content))
    print(markdown_content)
    print("-------------------------------------------")

    new_msg = Cutter()._reduce(markdown_content, 750)
    print(new_msg)
    print(len(new_msg))
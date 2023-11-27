import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import tqdm
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.utils import download_yandex_disk

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

QUERIES_URL = "https://disk.yandex.ru/d/yQt-jfBSzTs1eA"
QUERIES_PATH = "data/queries.txt"


@dataclass
class Node:
    """
    Represents a Trie node.

    Attributes
    ----------
    children : Dict[str, "Node"]
        Dictionary of child nodes.
    is_end : bool
        Indicates if this node is an ending character of a stored string.
    value : float
        Value associated with the stored string.
    """

    children: Dict[str, "Node"] = field(default_factory=dict)
    is_end: bool = False
    value: float = 0


@dataclass
class Trie:
    """
    A Trie data structure for efficient string manipulation and retrieval.

    Attributes
    ----------
    root : Node
        The root node of the Trie.
    """

    root: Node = field(default_factory=Node)

    def add_query(self, query: str, value: float) -> None:
        node = self.root
        for char in query:
            if char not in node.children:
                node.children[char] = Node()
            node = node.children[char]
        node.is_end = True
        node.value = value

    def remove_query(self, query: str) -> None:
        def remove_recursively(node, query, depth):
            if depth == len(query):
                if not node.is_end:
                    raise Exception(f"Query {query} not found!")
                node.is_end = False
                return len(node.children) == 0

            char = query[depth]
            if char not in node.children:
                raise Exception(f"Query {query} not found!")

            should_delete_child_node = remove_recursively(node.children[char], query, depth + 1)

            if should_delete_child_node:
                del node.children[char]
                return len(node.children) == 0

            return False

        remove_recursively(self.root, query, 0)

    def clear(self) -> None:
        self.root = Node()

    def suffixes(self, prefix: str) -> List[Tuple[float, str]]:
        def find_node(node, prefix):
            for char in prefix:
                if char in node.children:
                    node = node.children[char]
                else:
                    return None
            return node

        def collect_suffixes(node, prefix, results):
            if node.is_end:
                results.append((node.value, prefix))
            for char, child_node in node.children.items():
                collect_suffixes(child_node, prefix + char, results)

        results = []
        node = find_node(self.root, prefix)
        if node:
            collect_suffixes(node, prefix, results)
        return results

    def count_queries(self) -> int:
        def count_nodes(node):
            count = 1 if node.is_end else 0
            for child in node.children.values():
                count += count_nodes(child)
            return count

        return count_nodes(self.root)

    def print_trie(self, node=None, prefix=""):
        if node is None:
            node = self.root
        if node.is_end:
            print(f"String: {prefix}, Value: {node.value}")
        for char, next_node in node.children.items():
            self.print_trie(next_node, prefix + char)


@dataclass
class ReversedTrie(Trie):
    """
    A Reversed Trie data structure derived from the Trie,
    which efficiently manipulates and retrieves reversed strings.

    Give a possibility to find prefixes of the given suffix.

    Notes
    -----
    The ReversedTrie is derived from the Trie class, which means that
    all the methods of the Trie class are available for the ReversedTrie class.

    Use super() to call the methods of the Trie class.
    """

    def add_query(self, query: str, value: float) -> None:
        """
        Adds a single reversed query string to the Trie.

        Parameters
        ----------
        query : str
            The string whose reverse will be added to the Trie.
        value : float
            The value associated with the query.

        Examples
        --------
        Given queries: "apple", "triple"

        # >>> rtrie = ReversedTrie()
        # >>> rtrie.add_query("apple", 1.0)
        """
        # reversed_query = query[::-1]
        # super().add_query(reversed_query, value)
        for i in range(1, len(query) + 1):
            super().add_query(query[:i][::-1], value)

    def prefixes(self, suffix: str) -> List[Tuple[float, str]]:
        """
        Returns all prefixes of the given suffix.

        Notes
        -----
        Here by prefix we mean string prefix + suffix.

        Parameters
        ----------
        suffix : str
            The suffix string.

        Returns
        -------
        List[Tuple[float, str]]
            List of (value, prefix) pairs.

        Examples
        --------
        """
        reversed_suffix = suffix[::-1]
        suffixes = super().suffixes(reversed_suffix)

        return [(value, prefix[::-1]) for value, prefix in suffixes]


@dataclass
class Suggester:
    """
    A class to provide string suggestions based on input
    using both standard and reverse Trie data structures.

    Notes
    -----
    Make sure that suggest_ methods return unique suggests Tuple.

    Attributes
    ----------
    trie : Trie
        A standard trie data structure for forward string manipulations.
    reversed_trie : ReversedTrie
        A reverse trie data structure for backward string manipulations.
    """

    trie: Trie = field(default_factory=Trie)
    reversed_trie: ReversedTrie = field(default_factory=ReversedTrie)

    def fit(self, queries: Dict[str, float]) -> None:
        """
        Fits the suggester with a dictionary of queries and associated values.

        Parameters
        ----------
        queries : Dict[str, float]
            A dictionary of query strings and their associated values.
        """
        # for query, value in queries.items():
        #     self.trie.add_query(query, value)
        #
        #     # Добавляем все префиксы в обратном порядке в ReversedTrie
        #     for i in range(1, len(query) + 1):
        #         reversed_prefix = query[:i] #[::-1]  # Берем префикс и разворачиваем его
        #         self.reversed_trie.add_query(reversed_prefix, value)
        for query, value in queries.items():
            self.trie.add_query(query, value)
            self.reversed_trie.add_query(query, value)

    def count_queries(self) -> int:
        """
        Returns the total number of queries in both tries.

        Returns
        -------
        int
            Total number of queries.
        """
        return self.trie.count_queries() + self.reversed_trie.count_queries()

    def suggest_query(self, query: str) -> List[Tuple[float, str]]:
        """
        Provides suggestions based on a given query string.

        Also provides suggestions based on ReversedTrie prefixes.

        Hint
        ----
        Use the ReversedTrie prefixes method.

        Parameters
        ----------
        query : str
            The input string.

        Returns
        -------
        List[Tuple[float, str]]
            A list of suggested queries with their associated values.

        Examples
        --------
        # >>> suggester = Suggester()
        # >>> suggester.fit({"apple": 1.0, "triple": 2.0})
        # >>> suggester.suggest_query("pl")
        [(1.0, 'apple'), (2.0, 'triple')]
        """

        suggestions = []

        # Получаем предложения из основного Trie
        suggestions.extend(self.trie.suffixes(query))

        # Используем ReversedTrie для поиска префиксов, соответствующих суффиксу запроса
        reversed_trie_prefixes = self.reversed_trie.prefixes(query)

        # Для каждого префикса, найденного в ReversedTrie, ищем соответствующие строки в основном Trie
        for _, prefix in reversed_trie_prefixes:
            suggestions.extend(self.trie.suffixes(prefix))

        return suggestions

    def suggest_removed_char(self, query: str) -> List[Tuple[float, str]]:
        """
        Provides suggestions based on the query after removing the last character.

        Return [] if the query length is less than 2.

        Hint
        ----
        Reuse self.suggest_query instead of justs self.trie.suffixes.

        Parameters
        ----------
        query : str
            The input string.

        Returns
        -------
        List[Tuple[float, str]]
            A list of suggested queries with their associated values.
        """
        if len(query) < 2:
            return []
        return self.suggest_query(query[:-1])

    def suggest_last_words(self, query: str) -> List[Tuple[float, str]]:
        """
        Provides suggestions based on query words prefix.

        Parameters
        ----------
        query : str
            The input string, typically containing multiple words.

        Returns
        -------
        List[Tuple[float, str]]
            A list of suggested queries with their associated values.

        Examples
        --------
        Psuedo code:
        query = "apple iphone banana"
        suggestions =
            + suggest_query("apple iphone")
            + suggest_query("apple")
        """
        words = query.split()
        suggestions = set()
        for i in range(len(words)):
            sub_query = " ".join(words[i:])
            suggestions.update(self.suggest_query(sub_query))
        return sorted(suggestions, key=lambda x: -x[0])


    def suggest_each_word(self, query: str) -> List[Tuple[float, str]]:
        """
        Provides suggestions based on each word in the query.

        Parameters
        ----------
        query : str
            The input string, typically containing multiple words.

        Returns
        -------
        List[Tuple[float, str]]
            A list of suggested queries with their associated values.

        Examples
        --------
        Psuedo code:
        query = "apple iphone banana"
        suggestions =
            + suggest_query("apple")
            + suggest_query("iphone")
            + suggest_query("banana")
        """
        words = query.split()
        suggestions = set()
        for word in words:
            suggestions.update(self.suggest_query(word))
        return sorted(suggestions, key=lambda x: -x[0])

suggester = Suggester()

def preprocess_query(query: str) -> str:
    """
    Preprocess the given query string.

    Based on the queries.txt file understand
    how to preprocess the query string.

    Parameters
    ----------
    query : str
        The raw input string that needs to be preprocessed.

    Returns
    -------
    str
        The preprocessed query string.

    Examples
    --------
    # >>> preprocess_query("  HelLo,  ;  World!  ")
    'hello world'
    """
    query = re.sub(r'[^\w\s]', '', query)  # Удаляем пунктуацию
    query = re.sub(r'\s+', ' ', query)    # Удаляем лишние пробелы
    return query.strip().lower()


def count_queries(file) -> Dict[str, float]:
    """
    Counts the number of times each query appears in the file.

    The value of each query is defined by number of times
    the preprocess query (preprocess_query(q)) appears in the file.

    Parameters
    ----------
    file : file

    Returns
    -------
    Dict[str, float]
        A dictionary of query strings and their associated values.

    Examples
    --------
    file:
        appLe 123
        apple  123;
        bana;na
        banana
        bananA
    # >>> with open("queries.txt", "r") as file:
    # >>>     count_queries(file)
    {'apple 123': 2.0, 'banana': 3.0}
    """
    queries: Dict[str, float] = defaultdict(lambda: 0)
    rows = file.readlines()
    for line in tqdm.tqdm(rows):
        preprocessed_query = preprocess_query(line)
        queries[preprocessed_query] += 1.0
    return queries


@app.on_event("startup")
async def startup_event() -> None:
    """
    Handles the startup event of the FastAPI application.
    Downloads the queries file and fit the suggester with the queries.

    The value of each query is defined by number of times
    the preprocess query (preprocess_query(q)) appears in the file.
    """
    # download the queries file
    print("Downloading queries file...")
    download_yandex_disk(QUERIES_URL, QUERIES_PATH)
    with open(QUERIES_PATH, "r") as file:
        queries = count_queries(file)
    suggester.fit(queries)
    print(f"Suggester fitted with {suggester.count_queries()} queries!")


@app.get("/suggest/")
def suggest(query: str, k: int = 10):
    """
    Provide search query suggestions based on the input query.

    Suggestions are sorted by their associated values in descending order.

    Parameters
    ----------
    query : str
        The input search query for which suggestions are needed.
    k : int, optional
        The number of suggestions required, by default 10.

    Returns
    -------
    Dict[str, List[str]]
        A dictionary containing the preprocessed query and the list of suggestions.

    Examples
    --------
    # >>> suggestions("", k=10)
    {"query": "", "suggestions": []}
    # >>> suggestions("HeL", k=3)
    {"query": "hel", "suggestions": ["hello world", "help", "helmet"]}
    """

    if query == "":
        return {"query": "", "suggestions": []}

    query = preprocess_query(query)
    suggestions = []

    # Накапливаем предложения
    suggestions.extend(suggester.suggest_query(query))
    suggestions.extend(suggester.suggest_removed_char(query))
    if len(suggestions) < k:
        suggestions.extend(suggester.suggest_last_words(query))
        suggestions.extend(suggester.suggest_each_word(query))

    # Удаление дубликатов и сортировка
    unique_suggestions = list(dict.fromkeys(suggestions))
    sorted_unique_suggestions = sorted(unique_suggestions, key=lambda x: -x[0])[:k]

    return {"query": query, "suggestions": [s[1] for s in sorted_unique_suggestions]}

@app.get("/")
def root(request: Request):
    """
    Returns html page of the application.

    Parameters
    ----------
    request : Request
        The request object.
    """
    return templates.TemplateResponse("index.html", {"request": request})

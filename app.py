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
        """
        Adds a single query string to the Trie.

        Parameters
        ----------
        query : str
            The string to be added to the Trie.
        value : float
            The value associated with the query.
        """
        ...

    def remove_query(self, query: str) -> None:
        """
        Removes a single query string from the Trie.

        Parameters
        ----------
        query : str
            The string to be removed from the Trie.

        Raises
        ------
        Exception:
            If the query is not found in the Trie.

        >>> raise Exception(f"Query {query} not found!")
        """
        ...

    def clear(self) -> None:
        """Clears all the entries in the Trie."""
        ...

    def suffixes(
        self,
        prefix: str,
    ) -> List[Tuple[float, str]]:
        """
        Returns all suffixes of the given prefix.

        Notes
        -----
        Here by suffix we mean string prefix + suffix.

        Parameters
        ----------
        prefix : str
            The prefix string.

        Returns
        -------
        List[Tuple[float, str]]
            List of (value, suffix) pairs.

        Examples
        --------
        Given queries: "apple", "app", "application", "triple"

        >>> trie = Trie()
        >>> trie.add_query("apple", 1.0)
        >>> trie.add_query("app", 2.0)
        >>> trie.add_query("application", 3.0)
        >>> trie.add_query("triple", 4.0)
        >>> trie.suffixes("app")
        [(3.0, 'application'), (2.0, 'app'), (1.0, 'apple')]
        """
        ...

    def count_queries(self) -> int:
        """
        Returns the number of queries stored in the Trie.

        Returns
        -------
        int
            The number of queries stored in the Trie.
        """
        return 0


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

        >>> rtrie = ReversedTrie()
        >>> rtrie.add_query("apple", 1.0)
        """
        ...

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
        >>> rtrie = ReversedTrie()
        >>> rtrie.add_query("apple", 1.0)
        >>> ... # add more queries from apple
        >>> rtrie.add_query("triple", 2.0)
        >>> ... # add more queries from triple
        >>> rtrie.prefixes("pl")
        [(2.0, 'tripl'), (1.0, 'appl')] # "pl" is common
        """
        ...


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
        for q, v in queries.items():
            # fit trie with preprocessed queries
            ...

            # fit reversed trie with preprocessed queries
            # each query is used to fit the trie with all its ...
            ...
            ...

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
        >>> suggester = Suggester()
        >>> suggester.fit({"apple": 1.0, "triple": 2.0})
        >>> suggester.suggest_query("pl")
        [(1.0, 'apple'), (2.0, 'triple')]
        """
        # normal trie suffixes
        suggestions = self.trie.suffixes(query)

        # reversed trie prefixes
        ...

        suggestions = list(set(suggestions))

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
        return []

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
        return []

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
        return []


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
    >>> preprocess_query("  HelLo,  ;  World!  ")
    'hello world'
    """

    ...

    return query


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
    >>> with open("queries.txt", "r") as file:
    >>>     count_queries(file)
    {'apple 123': 2.0, 'banana': 3.0}
    """
    queries: Dict[str, float] = defaultdict(lambda: 0)
    rows = file.readlines()
    for q in tqdm.tqdm(rows):
        ...
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

    # load the queries file
    with open(QUERIES_PATH, "r") as file:
        queries = count_queries(file)

    # fit the suggester with the queries
    ...

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
    >>> suggestions("", k=10)
    {"query": "", "suggestions": []}
    >>> suggestions("HeL", k=3)
    {"query": "hel", "suggestions": ["hello world", "help", "helmet"]}
    """
    ...

    query = preprocess_query(query)

    # suggestions = ["hello world", ...] -> suggestions = []
    suggestions = ["hello world", "help", "helmet", "hello"]

    # full query + substring search suggestions
    ...

    # remove the last character of the query and then suggest
    ...

    # only if there are less than unique k suggestions
    if len(set(suggestions)) < k:
        # N-last words suggestions
        ...

        # each word suggestions
        ...

    # sorting by value and taking top k
    ...

    return {"query": query, "suggestions": suggestions}


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

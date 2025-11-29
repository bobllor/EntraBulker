from typing import Any, Callable
from support.types import Response, HeaderMap
import pandas as pd
import support.utils as util

class Parser:
    def __init__(self, df: pd.DataFrame):
        '''Class used to modify, validate, and parse an Excel file.
        
        Parameters
        ----------
            df: pd.DataFrame
                The DataFrame, Parser creates a deep copy of the given DataFrame.
        '''
        self.df: pd.DataFrame = df.copy(deep=True)

        # lower all column names.
        self.df.rename(mapper=lambda x: x.lower(), axis=1, inplace=True)

    def validate(self, default_headers: HeaderMap) -> Response:
        '''Validate the DataFrame and its headers. It will return a Response indicating an
        error/success and a message with the error if applicable.
        
        Parameters
        ----------
            default_headers: dict[str, str]
                Dictionary that maps internal variable names to user-defined names. The keys
                are the internal names, the values are user-defined names. Used to validate
                column headers.
        '''
        func_dict: dict[int, dict[str, Any]] = {
            0: {"func": self._check_duplicate_headers, "args": default_headers},
            1: {"func": self._check_duplicate_columns, "args": None},
            2: {"func": self._check_df_columns, "args": default_headers},
        }

        res: Response = util.generate_response(message="")

        for i in range(len(func_dict)):
            func: Callable = func_dict[i]["func"]
            args: HeaderMap | None = func_dict[i]["args"]

            if args is not None:
                res = func(args)
            else:
                res = func()

            if res["status"] == "error":
                return res

        res["message"] = "Successful validation"

        return res
    
    def fillna(self, column: str, value: Any) -> None:
        '''Replaces all NaN values on a target column with a value in place.'''
        column = column.lower()
        self.df[column] = self.df[column].fillna(value)
    
    def drop_empty_rows(self, col_name: str) -> None:
        '''Drop rows if a row is empty or NaN based on rows from a given column name. 
        The DataFrame is modified in place.
        '''
        bad_rows: list[int] = []

        for i, data in enumerate(self.get_rows(col_name)):
            if not isinstance(data, str):
                bad_rows.append(i)
        
        self.df.drop(index=bad_rows, axis=0, inplace=True)
    
    def dropna(self) -> int:
        '''Drops all NaN rows if any column has the value. This affects the entire DataFrame.
        
        It returns an int indicating how many rows were dropped, otherwise 0 if none.
        '''
        base_len: int = len(self.df)
        self.df = self.df.dropna(axis=0, how="any")

        new_len: int = len(self.df)

        return base_len - new_len
    
    def apply(self, col_name: str, *, func: Callable[[Any], Any], args: tuple = ()) -> None:
        '''Applies a function onto a column and replaces the column values in the DataFrame
        in place.

        Parameters
        ----------
            col_name: str
                The column name of the DataFrame.

            func: Callable
                A callable function, it must take one argument and returns one argument. 
            
            args: tuple, default ()
                A tuple of any data, used with args. By default it is an empty tuple.
        '''
        col_name = col_name.lower()
        self.df[col_name] = self.df[col_name].apply(func=func, args=args)
    
    def get_columns(self) -> list[str]:
        '''Returns a list of column names.'''
        return self.df.columns.to_list()
    
    def get_rows(self, col_name: str) -> list[Any]:
        '''Get rows from a DataFrame column in the form of a list.
        
        Parameters
        ----------
            col_name: str
                The column name of the DataFrame that represents the names column.
                It is not case sensitive.
        '''
        # the names are validated and corrected in validate_df.
        return self.df[col_name.lower()].to_list()
    
    def get_df(self) -> pd.DataFrame:
        return self.df
    
    def _check_duplicate_headers(self, headers: HeaderMap) -> Response:
        '''Checks the given HeaderMap for duplicate values. The HeaderMap will be reversed to
        value-key in order to validate and get the correct data from the DataFrame.
        
        If duplicate values are found, then an error Response will be returned.
        '''
        res: Response = util.generate_response(message="Successful Headers validation")
        seen: set[str] = set()

        for val in headers.values():
            seen.add(val)

        if len(seen) != len(headers):
            value_str: str = "value" if len(seen) == 1 else "values"
            res["message"] = f'Duplicate {value_str} "{", ".join([val for val in seen])}" found' \
                ', cannot have duplicate values: header values must be updated'
            res["status"] = "error"
        
        return res
    
    def _check_duplicate_columns(self) -> Response:
        '''Checks the DataFrame of the file for duplicate column names. This ensures that there will not be multiple
        same valued columns in a given file.

        It returns an Response with an error if found.
        '''
        seen_values: set[str] = set()
        duplicates: list[str] = []

        for val in self.df.columns:
            if val in seen_values:
                duplicates.append(val)

            seen_values.add(val)
        
        if len(duplicates) != 0:
            col_str: str = "columns found in the file" if len(duplicates) != 1 else "column found in the file"
            return util.generate_response("error", message=f"Duplicate {col_str}: {', '.join(duplicates)}")
        
        return util.generate_response(message="No duplicates found in the excel")

    def _check_df_columns(self, headers: dict[str, str]) -> Response:
        '''Checks the DataFrame columns to the reversed column map.'''
        # reverse to check the user defined names
        rev_column_map: dict = {v: k for k, v in headers.items()}

        found: set[str]= set()

        for col in self.df.columns:
            low_col: str = col.lower()

            if len(found) == len(rev_column_map):
                break

            if low_col in rev_column_map:
                found.add(low_col)

        if len(found) != len(headers):
            missing_columns: list[str] = [key for key in rev_column_map if key not in found]

            column_str: str = "column header" if len(missing_columns) == 1 else "column headers"

            return util.generate_response(status='error', message=f'File is missing {column_str}: {", ".join(missing_columns)}')

        return util.generate_response(status='success', message=f"Found columns {','.join(found)}")

    @property
    def length(self) -> int:
        '''The rows of the DataFrame.'''
        return len(self.df)
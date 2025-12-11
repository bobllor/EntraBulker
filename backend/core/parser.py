from typing import Any, Callable
import pandas as pd

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
    
    def add(self, column_name: str, data: pd.Series) -> None:
        '''Adds a Series to the DataFrame.'''
        self.df[column_name] = data
    
    def fillna(self, column: str, value: Any) -> None:
        '''Replaces all NaN values on a target column with a value in place.'''
        column = column.lower()
        self.df[column] = self.df[column].fillna(value)
    
    def drop_empty_rows(self, col_name: str) -> int:
        '''Drop rows if a row is empty or NaN based on rows from a given column name. 
        The DataFrame is modified in place.

        It returns the amount of rows dropped, if any.
        '''
        base_len: int = self.length
        bad_rows: list[int] = []

        for i, data in enumerate(self.get_rows(col_name)):
            # ensures that if a bad column is read or there are empty
            # cells (not NaN), then its dropped.
            if not isinstance(data, str) or data.strip() == "":
                bad_rows.append(i)
        
        self.df.drop(index=bad_rows, axis=0, inplace=True)

        new_length: int = self.length

        return base_len - new_length
    
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
    
    def create_series(self, func: Callable[[Any], pd.Series], args: tuple[Any]) -> pd.Series:
        '''Creates a Series.

        Parameters
        ----------
            func: Callable[[Any], pd.Series]
                A function used to perform with the given arguments. This must return a pd.Series.

            args: tuple[Any]
                Any arguments passed into the function.
        '''
        series: pd.Series = func(*args)

        return series

    @property
    def length(self) -> int:
        '''The rows of the DataFrame.'''
        return len(self.df)
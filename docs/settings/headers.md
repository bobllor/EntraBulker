# Headers Settings

The Headers settings contains the mapping for the column names of the file, this allows the
program to extract the data from the file and generate the output files.

The column values are ***case insensitive***.

# Column Values

There are four column values:
1. Name
2. Organization
3. First Name
4. Last Name

## Name

Default value: `full name`

The column representing the *full name* of the user. 

It is expected to be two names or more. If thereis only a single name value in this column, 
that name will be repeated twice in the final output.

## Organization

Default value: `operating company`

The column representing the *organization* of the user. 

This ***does not*** have to be an organization value or any other related values. The values are used
for *mapping domain names* to the user of the row. 

It is used with the key-value pairs defined in the [Organization settings tab](./organization.md).

## First Name

Default value: `first name`

The column representing the *first name* of the user.

## Last Name

Default value: `last name`

The column representing the *last name* of the user.
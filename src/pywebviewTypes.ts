/* 
These will need to be updated manually whenever types.py is updated in the backend.
The related types found in both files must be 1:1.
*/

// obtained from types in the backend
export type APISettings = {
    output_dir: string,
    flatten_csv: boolean,
    template: TemplateMap,
    format: Formatting,
    password: Password,
}

export type TemplateMap = {
    enabled: boolean,
    text: string,
    words_to_replace: string,
}

export type Formatting = {
    format_type: FormatType,
    format_case: FormatCase,
    format_style: FormatStyle,
}

export type Response = {
    status: "success" | "error",
    message: string,
    [key: string]: any,
}

// by default lowercase and numbers are enabled, it will not be
// available to get modified.
export type Password = {
    length: number,
    use_uppercase: boolean,
    use_punctuations: boolean,
}

export type FormatType = "period" | "no space";
export type FormatCase = "title" | "upper" | "lower";
export type FormatStyle = "first last" | "f last" | "first l";
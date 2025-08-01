@load base/frameworks/files
@load base/files/extract

module FileExtraction;

export {
    # Path for file extraction - use absolute path
    const extraction_path = "/Users/russellsmith/zeek_yara_integration/extracted_files/" &redef;
}

event zeek_init()
{
    # Register for common MIME types
    local mime_types: set[string] = {
        "application/x-dosexec",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip"
    };
    
    Files::register_for_mime_types(Files::ANALYZER_EXTRACT, mime_types);
}

event file_new(f: fa_file)
{
    Files::add_analyzer(f, Files::ANALYZER_EXTRACT,
        [$extract_filename=fmt("%s%s", extraction_path, f$id)]);
}

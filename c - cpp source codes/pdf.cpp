#include <mupdf/fitz.h>
#include <string>
#include <iostream>

int main()
{
    // Open the PDF file
    fz_context *ctx = fz_new_context(NULL, NULL, FZ_STORE_UNLIMITED);
    fz_document *doc = fz_open_document(ctx, "D:\\dgbdata\\20221130-statements-5930-.pdf");

    // Loop through the pages and extract the text
    std::string text;
    int pageCount = fz_count_pages(ctx, doc);
    for (int i = 0; i < pageCount; ++i)
    {
        fz_page *page = fz_load_page(ctx, doc, i);
        fz_stext_page *textPage = fz_new_stext_page_from_page(ctx, page, NULL);
        fz_stext_block *block;
        for (block = textPage->first_block; block; block = block->next)
        {
            if (block->type == FZ_STEXT_BLOCK_TEXT)
            {
                for (fz_stext_line *line = block->u.t.first_line; line; line = line->next)
                {
                    for (fz_stext_char *ch = line->first_char; ch; ch = ch->next)
                    {
                        text += ch->c;
                    }
                    text += '\n';
                }
            }
        }
        fz_drop_stext_page(ctx, textPage);
        fz_drop_page(ctx, page);
    }

    // Close the document and clean up
    fz_drop_document(ctx, doc);
    fz_drop_context(ctx);

    // Print the extracted text
    std::cout << text << std::endl;

    return 0;
}


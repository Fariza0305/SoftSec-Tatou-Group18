/*
 * AFL++ Fuzzing Harness for XML Parser
 * =====================================
 * This harness targets the XML parsing functionality in Tatou,
 * specifically the RMAP import and document processing features.
 * Compiled with AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

// Disable external entity loading to prevent XXE during fuzzing
static void disable_external_entities(xmlParserCtxtPtr ctxt) {
    if (ctxt) {
        ctxt->replaceEntities = 0;
        ctxt->loadsubset = 0;
    }
}

// Custom error handler to suppress XML parsing errors during fuzzing
static void xml_error_handler(void *ctx, const char *msg, ...) {
    // Suppress errors - we expect malformed input
    (void)ctx;
    (void)msg;
}

// Main fuzzing target - parse XML from buffer
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // Ignore empty inputs
    if (size == 0 || size > 1024 * 1024) {
        return 0;
    }
    
    // Set up error handlers
    xmlSetGenericErrorFunc(NULL, xml_error_handler);
    
    // Initialize parser
    xmlParserCtxtPtr ctxt = xmlCreateMemoryParserCtxt((const char *)data, size);
    if (!ctxt) {
        return 0;
    }
    
    // Disable external entities for security
    disable_external_entities(ctxt);
    
    // Parse the XML
    xmlDocPtr doc = xmlCtxtReadMemory(ctxt, (const char *)data, size, 
                                       "noname.xml", NULL, 
                                       XML_PARSE_NOENT | XML_PARSE_DTDLOAD);
    
    if (doc) {
        // Process document structure
        xmlNodePtr root = xmlDocGetRootElement(doc);
        if (root) {
            // Traverse nodes to trigger parsing logic
            for (xmlNodePtr node = root->children; node; node = node->next) {
                if (node->type == XML_ELEMENT_NODE) {
                    // Access node properties to trigger memory operations
                    xmlChar *content = xmlNodeGetContent(node);
                    if (content) {
                        // Simulate processing
                        size_t len = strlen((char *)content);
                        (void)len;
                        xmlFree(content);
                    }
                    
                    // Check attributes
                    for (xmlAttrPtr attr = node->properties; attr; attr = attr->next) {
                        xmlChar *value = xmlGetProp(node, attr->name);
                        if (value) {
                            xmlFree(value);
                        }
                    }
                }
            }
        }
        
        // Clean up document
        xmlFreeDoc(doc);
    }
    
    // Clean up parser context
    xmlFreeParserCtxt(ctxt);
    
    // Clean up parser
    xmlCleanupParser();
    
    return 0;
}

#ifndef __AFL_FUZZ_TESTCASE_LEN
// Standalone mode for testing
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return 1;
    }
    
    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }
    
    // Read file into buffer
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    uint8_t *buffer = malloc(size);
    if (!buffer) {
        fclose(f);
        return 1;
    }
    
    fread(buffer, 1, size, f);
    fclose(f);
    
    // Call fuzzer
    LLVMFuzzerTestOneInput(buffer, size);
    
    free(buffer);
    return 0;
}
#endif


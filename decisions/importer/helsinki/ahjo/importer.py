from .scanner import scan_dir


class ChangeImporter(object):
    def import_changes(self, root='/files'):
        """
        Detect changes on the server and import them.

        :type root: str
        :param root: The root directory of the files to import
        """
        doc_infos = scan_dir(root, max_depth=9999)
        for doc_info in doc_infos:
            if self.should_import(doc_info):
                self._import_single(doc_info)

    def _import_single(self, doc_info):
        old_version = self.get_imported_version(doc_info)
        new_version = doc_info.mtime_text
        if not old_version:
            self.handle_document_added(doc_info)
            self.set_imported_version(doc_info, new_version)
        elif old_version != new_version:
            self.handle_document_changed(doc_info)
            self.set_imported_version(doc_info, new_version)

    def should_import(self, doc_info):
        """
        Return true if given document should be imported.

        :type doc_info: .docinfo.DocumentInfo
        :rtype: bool
        """
        return True

    def get_imported_version(self, doc_info):
        """
        Get the last imported version of a document.

        :type doc_info: .docinfo.DocumentInfo
        :rtype: str|None
        """
        return None

    def set_imported_version(self, doc_info, version):
        """
        Set the last imported version of a document.

        :type doc_info: .docinfo.DocumentInfo
        :type version: str
        """
        pass

    def handle_document_added(self, doc_info):
        """
        Handle a new document being added.

        :type doc_info: .docinfo.DocumentInfo
        """
        self.handle_document_changed(doc_info)

    def handle_document_changed(self, doc_info):
        """
        Handle a document being changed.

        :type doc_info: .docinfo.DocumentInfo
        """
        pass

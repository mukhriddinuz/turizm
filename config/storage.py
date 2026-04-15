from whitenoise.storage import CompressedManifestStaticFilesStorage


class NoSourceMapManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Ignore sourceMappingURL references during collectstatic.

    Some third-party packages ship minified CSS/JS files without the matching
    .map files. WhiteNoise tries to rewrite those references and raises
    MissingFileError. We keep normal asset hashing, but skip source map
    rewriting so collectstatic can complete successfully.
    """

    patterns = tuple(
        (
            extension,
            tuple(
                pattern
                for pattern in extension_patterns
                if "sourceMappingURL"
                not in (
                    pattern[0]
                    if isinstance(pattern, (tuple, list))
                    else pattern
                )
            ),
        )
        for extension, extension_patterns in CompressedManifestStaticFilesStorage.patterns
    )

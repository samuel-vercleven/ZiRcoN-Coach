pragma Singleton
import QtQuick

QtObject {
    property bool belveth: initialTheme === "belveth"
    // Keep the accepted turquoise design exactly intact; this is display only.
    function color(original) {
        return belveth ? (violet[original.toLowerCase()] || original) : original;
    }
    readonly property var violet: ({
        "#09131f": "#100b1b", "#09121e": "#0c0914",
        "#0d1928": "#150e22", "#101f30": "#1b1230", "#12192b": "#21132f",
        "#0f1b28": "#181123", "#182938": "#2a1e3b", "#162a3b": "#261a37",
        "#142535": "#20162f", "#132331": "#20172e", "#132636": "#2a1b3a",
        "#152638": "#251932", "#203346": "#38264c", "#203448": "#352446",
        "#20384a": "#372348", "#223d49": "#3c2853", "#1e3549": "#352344",
        "#183a4b": "#352249", "#19393e": "#352449", "#1a3940": "#37274b",
        "#1c3d45": "#352943", "#2b2d43": "#36213d", "#1b3e48": "#442e5a",
        "#244b50": "#49335f", "#233a4c": "#382a49", "#244452": "#403052",
        "#263c4e": "#44324e", "#253a4d": "#3c2c4c", "#27384a": "#3b2a4a",
        "#2a3d50": "#4a365a", "#304458": "#51405f", "#30485d": "#534065",
        "#314356": "#503d5e", "#355b70": "#80604c", "#366b70": "#8968b0",
        "#376986": "#a878d2", "#447d87": "#9b7bb4", "#5192a0": "#b59c71",
        "#496078": "#71607f", "#498d8d": "#a184bd", "#3885b7": "#8256b1",
        "#5b748c": "#8c729e", "#6488a7": "#a17aba",
        "#0a8170a8": "#146f48bc", "#101a7381": "#227840b8",
        "#10376379": "#283e1c62", "#13394a61": "#33482b72", "#22456d78": "#44382558",
        "#062a2b": "#21132f", "#58dfc0": "#c5a6fa", "#8bfadd": "#dbc6ff",
        "#6cf1d2": "#dfc8ff", "#b6ffee": "#eadbff", "#65d8c5": "#c6a2f8",
        "#70ebcf": "#ceb0ff", "#70e1cc": "#d0b4f1", "#71d7ca": "#cab0ee",
        "#73e4c8": "#d8baff", "#74c6c9": "#dbbd80", "#75e7d0": "#e5c486",
        "#76e7cf": "#caa8f6", "#78e4ce": "#d5bafa", "#7ce8d5": "#dfc6ff",
        "#7ee4cb": "#d0b2f3", "#75e0ca": "#d6b4fa", "#93e2d5": "#d5c0ee",
        "#66e3c8": "#dfc18a", "#74dec9": "#dfc18a", "#7de8cf": "#e6c893",
        "#62e6c5": "#e5c486",
        "#758ea7": "#9885ac", "#8aa3bd": "#ac99c0", "#8ca4bb": "#ad9bc2",
        "#8daac4": "#b29ec8", "#8fa9c2": "#b09dc4", "#92a9c1": "#b29fc4",
        "#94adc2": "#b5a3c8", "#95acc3": "#b5a3c8", "#96adc5": "#b7a5cb",
        "#97b2c9": "#baa9d0", "#98b8c6": "#bcaad0", "#99b1c8": "#b9a6cc",
        "#9db3c9": "#bba8d0", "#9db8cf": "#bdabd3", "#9fb7cc": "#beacd1",
        "#9fb7ce": "#beacd1", "#9fb7cf": "#beacd1", "#9fbfcd": "#c0acd1",
        "#a1b9d0": "#c1afd4", "#a1c3ca": "#c3b0d1", "#a2bdd2": "#c2b0d5",
        "#a3b7cc": "#c2b0d3", "#a3bac5": "#bfaecf", "#a4bad0": "#c3b1d5",
        "#a6b9cb": "#c5b5d7", "#a6bdd3": "#c5b5d8", "#a6bfd2": "#c6b4d7",
        "#a6bfd3": "#c6b4d7", "#a6c2d3": "#c8b5da", "#a7bcd0": "#c5b3d7",
        "#a8bfd3": "#c7b6d9", "#a8c0d4": "#c7b6d9", "#aac1d6": "#c9b8dd",
        "#acc4d7": "#cbbade", "#adc3d6": "#ccbbdf", "#adc5ce": "#ccb7dc",
        "#afc9d4": "#cfbddf", "#b1c5d8": "#d0c0e4", "#b1c6d9": "#d0c0e4",
        "#b2c6d6": "#d1c0e2", "#b2c7d9": "#d1c0e3", "#b4cfdd": "#d5c4e6",
        "#bad0de": "#dbcaec", "#c3d2e3": "#ded0ef", "#c3d3e3": "#ded0ef",
        "#c4d8e3": "#e0d0ef", "#cad7e6": "#e2d5f0", "#edf3fa": "#f5efff"
    })
}

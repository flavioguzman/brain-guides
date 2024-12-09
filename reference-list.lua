function Div (div)
    if div.classes[1] == "references" then
        -- Add a class that we can style as a list
        div.classes:insert("reference-list")
        -- Simplified CSS styling for mobile-friendliness
        div.attributes.style = [[
            list-style-type: none;
            padding-left: 1em;
        ]]
        
        -- Style each reference entry
        for _, item in ipairs(div.content) do
            if item.t == "Div" and item.classes[1] == "csl-entry" then
                item.attributes.style = [[
                    margin-bottom: 0.5em;
                    text-indent: -1em;
                    padding-left: 1em;
                ]]
            end
        end
        return div
    end
    return div
end
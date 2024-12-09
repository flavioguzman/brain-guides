function Image (img)
    img.caption = pandoc.List({})
    img.title = ""
    img.attributes.alt = ""
    return img
end

function Figure (fig)
    -- Remove the figure caption
    fig.caption = pandoc.List({})
    -- If there's an image inside the figure, remove its caption too
    if fig.content and fig.content[1] and fig.content[1].t == "Image" then
        fig.content[1].caption = pandoc.List({})
        fig.content[1].title = ""
        fig.content[1].attributes.alt = ""
    end
    return fig
end
                
# Mead & Hunt SeaMDLess

## Inspiration
`SeaMDLess` was inspired by the work of [Ashley Goldstein](https://www.youtube.com/@ashdotpy) and her [LWM Livestream OpenAI to Omniverse](https://www.youtube.com/watch?v=rC-MUK3ou6Q) Video. In it she goes through the process of connecting OpenAI DALL-E through it's API. During the video a viewer recommended that she integrate it into my Backplate tool.

Instead I am building it as a material generation tool.

## About
This tool was created so users can easily generate an MDL material based off of text to image prompting. Since it can be used to make seamless MDL I decided to call it `SeaMDLess`.

## Adding This Extension
To add this extension to your Omniverse app:
1. Go into: Extension Manager -> Gear Icon -> Extension Search Path
2. Add this as a search path: `git://github.com/ericcraft-mh/meadhunt-utility-seamdless.git?branch=main&dir=exts`

## To-Do List
- Implement Stable Diffusion option.
- Implement DeepBump to generate normal and height from image.

## App Link Setup
If `app` folder link doesn't exist or broken it can be created again. For better developer experience it is recommended to create a folder link named `app` to the *Omniverse Kit* app installed from *Omniverse Launcher*. Convenience script to use is included.

Run:

```
> link_app.bat
```

If successful you should see `app` folder link in the root of this repo.

If multiple Omniverse apps is installed script will select recommended one. Or you can explicitly pass an app:

```
> link_app.bat --app create
```

You can also just pass a path to create link to:

```
> link_app.bat --path "C:/Users/bob/AppData/Local/ov/pkg/create-2021.3.4"
```

## Contributing
The source code for this repository is provided as-is, but I am accepting outside contributions.

Issues, Feature Requests, and Pull Requests are welcomed.


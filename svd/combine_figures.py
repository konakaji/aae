from PIL import Image
import svd.constant as const


def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def fig_row(i):
    im1 = Image.open('{}/{}.png'.format(const.FINAL_FIGURE_PATH, i))
    im2 = Image.open('{}/{}.png'.format(const.FINAL_FIGURE_PATH, 100 + i))
    im3 = Image.open('{}/cost_{}.png'.format(const.FINAL_FIGURE_PATH, i))
    return get_concat_h(get_concat_h(im1, im2), im3)


if __name__ == '__main__':
    images = []
    for i in range(0, 4):
        images.append(fig_row(i))
    result = None
    for i in range(0, 4):
        if result is None:
            result = images[i]
        else:
            result = get_concat_v(result, images[i])
    result.save("{}/concatinated.png".format(const.FINAL_FIGURE_PATH))
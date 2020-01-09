import logging
import os
import platform

import cv2
import mxnet as mx
import mxnet.gluon as gluon

from core import Prediction
from core import box_resize
from core import plot_bbox
from core import testdataloader

logfilepath = ""  # 따로 지정하지 않으면 terminal에 뜸
if os.path.isfile(logfilepath):
    os.remove(logfilepath)
logging.basicConfig(filename=logfilepath, level=logging.INFO)


def run(weight_path="exportweights",
        load_name="608_608_ADAM_PDark_53",
        load_period=100, GPU_COUNT=0,
        multiperclass=True,
        nms_thresh=0.5,
        nms_topk=500,
        except_class_thresh=0.05,
        plot_class_thresh=0.5,
        video_name="webcam",
        video_save_path="result_video",
        video_show=True,
        video_save=True):
    if video_save:
        if not os.path.exists(video_save_path):
            os.makedirs(video_save_path)

    if GPU_COUNT <= 0:
        ctx = mx.cpu(0)
    elif GPU_COUNT > 0:
        ctx = mx.gpu(0)

    # 운영체제 확인
    if platform.system() == "Linux":
        logging.info(f"{platform.system()} OS")
    elif platform.system() == "Windows":
        logging.info(f"{platform.system()} OS")
    else:
        logging.info(f"{platform.system()} OS")

    if GPU_COUNT > 0:
        free_memory, total_memory = mx.context.gpu_memory_info(0)
        free_memory = round(free_memory / (1024 * 1024 * 1024), 2)
        total_memory = round(total_memory / (1024 * 1024 * 1024), 2)
        logging.info(f'Running on {ctx} / free memory : {free_memory}GB / total memory {total_memory}GB')
    else:
        logging.info(f'Running on {ctx}')

    logging.info(f"test {load_name}")
    netheight = int(load_name.split("_")[0])
    netwidth = int(load_name.split("_")[1])
    if not isinstance(netheight, int) and not isinstance(netwidth, int):
        logging.info("height is not int")
        logging.info("width is not int")
        raise ValueError
    else:
        logging.info(f"network input size : {(netheight, netwidth)}")

    try:
        _, test_dataset = testdataloader()

    except Exception:
        logging.info("The dataset does not exist")
        exit(0)

    weight_path = os.path.join(weight_path, load_name)
    sym = os.path.join(weight_path, f'{load_name}_pre-symbol.json')
    params = os.path.join(weight_path, f'{load_name}_pre-{load_period:04d}.params')

    logging.info("symbol model test")
    try:
        net = gluon.SymbolBlock.imports(sym,
                                        ['data'],
                                        params, ctx=ctx)
    except Exception:
        # DEBUG, INFO, WARNING, ERROR, CRITICAL 의 5가지 등급
        logging.info("loading symbol weights 실패")
        exit(0)
    else:
        logging.info("loading symbol weights 성공")

    net.hybridize(active=True, static_alloc=True, static_shape=True)

    prediction = Prediction(
        from_sigmoid=False,
        num_classes=test_dataset.num_class,
        nms_thresh=nms_thresh,
        nms_topk=nms_topk,
        except_class_thresh=except_class_thresh,
        multiperclass=multiperclass)

    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    cap = cv2.VideoCapture(0)
    fps = cap.get(cv2.CAP_PROP_FPS)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    out = cv2.VideoWriter(os.path.join(video_save_path, f'{video_name}.avi'), fourcc, fps, (width, height))
    logging.info(f"real input size : {(height, width)}")

    while True:
        ret, image = cap.read()
        if ret:
            origin_image = image.copy()
            image = cv2.resize(image, (netwidth, netheight), interpolation=3)
            image[:, :, (0, 1, 2)] = image[:, :, (2, 1, 0)]  # BGR to RGB
            image = mx.nd.array(image, ctx=ctx)
            image = image.expand_dims(axis=0)

            output1, output2, output3, \
            anchor1, anchor2, anchor3, \
            offset1, offset2, offset3, \
            stride1, stride2, stride3 = net(image)

            ids, scores, bboxes = prediction(output1, output2, output3, anchor1, anchor2, anchor3, offset1, offset2,
                                             offset3, stride1, stride2, stride3)

            bbox = box_resize(bboxes[0], (netwidth, netheight), (width, height))
            result = plot_bbox(origin_image, bbox, scores=scores[0], labels=ids[0],
                               thresh=plot_class_thresh,
                               reverse_rgb=False,
                               class_names=test_dataset.classes)
            if video_save:
                out.write(result)
            if video_show:
                cv2.imshow(video_name, result)
                cv2.waitKey(1)

    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run(weight_path="exportweights",
        load_name="608_608_ADAM_PDark_53",
        load_period=200, GPU_COUNT=0,
        multiperclass=True,
        nms_thresh=0.5,
        nms_topk=500,
        except_class_thresh=0.05,
        plot_class_thresh=0.5,
        video_name="webcam",
        video_save_path="result_video",
        video_show=True,
        video_save=True)

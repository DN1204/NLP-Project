import pickle
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))

import tensorflow as tf
import numpy as np
from models import TextCnnModel
from predict_base import PredictorBase


class Predictor(PredictorBase):
    def __init__(self, config):
        super(Predictor, self).__init__(config)
        self.model = None
        self.config = config

        # 加载数据
        self.word_to_index = None
        self.label_to_index = None
        self.word_vectors = None
        self.vocab_size = None

        self.load_vocab()
        self.index_to_label = {value: key for key, value in self.label_to_index.items()}

        self.sequence_length = self.config["sequence_length"]

        # 创建模型
        self.create_model()
        # 加载计算图
        self.load_graph()

    def load_vocab(self):
        # 将词汇-索引映射表加载出来
        with open(os.path.join(self.output_path, "word_to_index.pkl"), "rb") as f:
            self.word_to_index = pickle.load(f)
            self.vocab_size = len(self.word_to_index)
        with open(os.path.join(self.output_path, "label_to_index.pkl"), "rb") as f:
            self.label_to_index = pickle.load(f)

        if os.path.exists(os.path.join(self.output_path, "word_vectors.npy")):
            self.word_vectors = np.load(os.path.join(self.output_path, "word_vectors.npy"))

    def sentence_to_idx(self, sentence):
        """
        将分词后的句子转换成idx表示
        :param sentence:
        :return:
        """
        sentence_ids = [self.word_to_index.get(token, self.word_to_index["<UNK>"]) for token in sentence]
        sentence_pad = sentence_ids[: self.sequence_length] if len(sentence_ids) > self.sequence_length \
            else sentence_ids + [0] * (self.sequence_length - len(sentence_ids))
        return sentence_pad

    def load_graph(self):
        """
        加载计算图
        :return:
        """
        self.sess = tf.Session()
        ckpt = tf.train.get_checkpoint_state(os.path.join(os.path.abspath(os.path.dirname(os.getcwd())),
                                                          self.config["ckpt_model_path"]))
        if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
            print('Reloading model parameters..')
            self.model.saver.restore(self.sess, ckpt.model_checkpoint_path)
        else:
            raise ValueError('No such file:[{}]'.format(self.config["ckpt_model_path"]))

    def create_model(self):
        """
                根据config文件选择对应的模型，并初始化
                :return:
                """
        if self.config["model_name"] == "textcnn":
            self.model = TextCnnModel(config=self.config, vocab_size=self.vocab_size, word_vectors=self.word_vectors)

    def predict(self, sentence):
        """
        给定分词后的句子，预测其分类结果
        :param sentence:
        :return:
        """
        sentence_ids = self.sentence_to_idx(sentence)

        prediction = self.model.infer(self.sess, [sentence_ids]).tolist()[0]
        label = []
        for idx, result in enumerate(prediction):
            if result == 1:
                label.append(self.index_to_label[idx])
        return label


